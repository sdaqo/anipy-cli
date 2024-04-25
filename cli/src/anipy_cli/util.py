import sys
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple

from InquirerPy import inquirer
from anipy_api.player import  get_player
from yaspin.core import Yaspin
from yaspin.spinners import Spinners

from anipy_api.anime import Anime
from anipy_api.provider import list_providers
from anipy_api.download import Downloader
from anipy_cli.config import Config
from anipy_cli.colors import cinput, color, colors, cprint

if TYPE_CHECKING:
    from anipy_api.provider import BaseProvider, Episode, ProviderStream
    from anipy_api.player import PlayerBase

def get_season_searches(gogo=True):
    searches = []
    selected = []
    season_year = None
    season_name = None
    while not season_year:
        try:
            season_year = int(cinput(colors.CYAN, "Season Year: "))
        except ValueError:
            print("Please enter a valid year.\n")

    while not season_name:
        season_name_input = cinput(
            colors.CYAN, "Season Name (spring|summer|fall|winter): "
        )
        if season_name_input.lower() in ["spring", "summer", "fall", "winter"]:
            season_name = season_name_input

        else:
            cprint(colors.YELLOW, "Please enter a valid season name.\n")

    with yaspin(
        text="Fetching seasonals...", spinner=Spinners.dots, color="cyan"
    ) as spinner:
        if gogo:
            anime_in_season = search_in_season_on_gogo(season_year, season_name)

        else:
            # anime_in_season = MAL().get_seasonal_anime(season_year, season_name)
            ...

        spinner.ok("✔")

    cprint("Anime found in {} {} Season: ".format(season_year, season_name))
    cprint(
        colors.CYAN,
        "Anime found in ",
        colors.GREEN,
        season_year,
        colors.CYAN,
        " ",
        colors.YELLOW,
        season_name,
        colors.CYAN,
        " Season: ",
    )
    anime_names = []
    for anime in anime_in_season:
        if gogo:
            anime_names.append(anime["name"])

        else:
            anime_names.append(anime["node"]["title"])

    print_names(anime_names)
    selection = cinput(colors.CYAN, "Selection: (e.g. 1, 1  3 or 1-3) \n>> ")
    if selection.__contains__("-"):
        selection_range = selection.strip(" ").split("-")
        for i in range(int(selection_range[0]) - 1, int(selection_range[1]) - 1, 1):
            selected.append(i)

    else:
        for i in selection.lstrip(" ").rstrip(" ").split(" "):
            selected.append(int(i) - 1)

    for value in selected:
        searches.append(anime_in_season[int(value)])
    return searches


class DotSpinner(Yaspin):
    def __init__(self, *text_and_colors, **spinner_args):
        super().__init__(
            text=color(*text_and_colors),
            color="cyan",
            spinner=Spinners.dots,
            **spinner_args,
        )

    def __enter__(self) -> "DotSpinner":
        self.start()
        return self

    def set_text(self, *text_and_colors):
        self.text = color(*text_and_colors)


def search_show_prompt() -> Optional["Anime"]:
    query = inquirer.text(
        "Search Anime:",
        long_instruction="To cancel this prompt press ctrl+z",
        mandatory=False,
    ).execute()

    if query is None:
        return None

    with DotSpinner("Searching for ", colors.BLUE, query, "..."):
        results: List[Anime] = []
        for provider in get_prefered_providers():
            results.extend(
                [
                    Anime.from_search_result(provider, x)
                    for x in provider.get_search(query)
                ]
            )

    if len(results) == 0:
        error("no search results")
        return search_show_prompt()

    anime = inquirer.fuzzy(
        message="Select Show:",
        choices=results,
        long_instruction="\nD = Anime is available in dub (or sub)\nTo skip this prompt press ctrl+z",
        mandatory=False,
    ).execute()

    return anime


def pick_episode_prompt(
    anime: "Anime", dub: bool, instruction: str = ""
) -> Optional["Episode"]:
    with DotSpinner("Fetching episode list for ", colors.BLUE, anime.name, "..."):
        episodes = anime.get_episodes(dub)

    return inquirer.fuzzy(
        message="Select Episode:",
        instruction=instruction,
        choices=episodes,
        long_instruction="To skip this prompt press ctrl+z",
        mandatory=False,
    ).execute()


def pick_episode_range_prompt(anime: "Anime", dub: bool) -> List["Episode"]:
    with DotSpinner("Fetching episode list for ", colors.BLUE, anime.name, "..."):
        episodes = anime.get_episodes(dub)

    res = inquirer.text(
        message=f"Input Episode Range(s) from episodes {episodes[0]} to {episodes[-1]}:",
        long_instruction="Type e.g. `1-10 19-20` or `3-4` or `3`\nTo skip this prompt press ctrl+z",
        mandatory=False,
    ).execute()

    if res is None:
        return []

    return parse_episode_ranges(res, episodes)


def dub_prompt(anime: "Anime") -> bool:
    config = Config()

    if not anime.has_dub or config.preferred_type == "sub":
        return False

    if config.preferred_type == "dub":
        return True

    res = inquirer.confirm("Want to watch in dub?").execute()
    print("Hint: you can set a default in the config with `preferred_type`!")

    return res


def get_prefered_providers() -> Iterator["BaseProvider"]:
    preferred_providers = Config().providers

    for i in list_providers():
        if i.NAME in preferred_providers:
            yield i()


def get_download_path(
    anime: "Anime",
    stream: "ProviderStream",
    parent_directory: Optional[Path] = None,
) -> Path:
    config = Config()
    download_folder = parent_directory or config.download_folder_path

    anime_name = Downloader._get_valid_pathname(anime.name)
    filename = config.download_name_format.format(
        show_name=anime_name,
        episode_number=stream.episode,
        quality=stream.resolution,
        provider=anime.provider.NAME,
        type="dub" if stream.dub else "sub",

    )

    filename = Downloader._get_valid_pathname(filename)  # type: ignore

    return download_folder / anime_name / filename


def parse_episode_ranges(ranges: str, episodes: List["Episode"]) -> List["Episode"]:
    picked = set()
    for r in ranges.split():
        numbers = r.split("-")
        if numbers[0] > numbers[-1]:
            error(f"invalid range: {r}")
            continue
            # return pick_episode_range_prompt(anime, dub)

        picked = picked | set(
            episodes[
                episodes.index(parsenum(numbers[0])) : episodes.index(
                    parsenum(numbers[-1])
                )
                + 1
            ]
        )

    return sorted(picked)


def parse_auto_search(passed: str) -> Tuple["Anime", bool, List["Episode"]]:
    options = iter(passed.split(":"))
    query = next(options, None)
    ranges = next(options, None)
    ltype = next(options, None)

    if not query:
        error("you provided the search parameter but no query", fatal=True)

    if not ranges:
        error("you provided the search parameter but no episode ranges", fatal=True)


    if not (ltype == "sub" or ltype == "dub"):
        ltype = Config().preferred_type
    
    with DotSpinner("Searching for ", colors.BLUE, query, "..."):
        results: List[Anime] = []
        for provider in get_prefered_providers():
            results.extend(
                [
                    Anime.from_search_result(provider, x)
                    for x in provider.get_search(query)
                ]
            )
    if len(results) == 0:
        error(f"no anime found for query {query}", fatal=True)

    result = results[0]
    episodes = result.get_episodes(dub=ltype == "dub")
    choosen = parse_episode_ranges(ranges, episodes)

    return result, ltype == "dub", choosen

def parsenum(n: str):
    try:
        return int(n)
    except ValueError:
        return float(n)


def find_closest(episodes: List["Episode"], target: int) -> "Episode":
    left, right = 0, len(episodes) - 1
    while left < right:
        if abs(episodes[left] - target) <= abs(episodes[right] - target):
            right -= 1
        else:
            left += 1

    return episodes[left]


def search_in_season_on_gogo(s_year, s_name):
    # page = 1
    # content = True
    # gogo_anime_season_list = []
    # while content:
    #     r = requests.get(
    #         f"{Config().gogoanime_url}/sub-category/{s_name}-{s_year}-anime",
    #         params={"page": page},
    #     )
    #     soup = BeautifulSoup(r.content, "html.parser")
    #     wrapper_div = soup.find("div", attrs={"class": "last_episodes"})
    #     try:
    #         anime_items = wrapper_div.findAll("li")
    #         for link in anime_items:
    #             link_a = link.find("p", attrs={"class": "name"}).find("a")
    #             name = link_a.get("title")
    #             gogo_anime_season_list.append(
    #                 {
    #                     "name": name,
    #                     "category_url": "{}{}".format(
    #                         Config().gogoanime_url, link_a.get("href")
    #                     ),
    #                 }
    #             )
    #
    #     except AttributeError:
    #         content = False
    #
    #     page += 1
    # filtered_list = filter_anime_list_dub_sub(gogo_anime_season_list)
    #
    # return filtered_list
    ...


def error(error: str, fatal: bool = False):
    if not fatal:
        sys.stderr.write(f"anipy-cli: error: {error}\n")
    else:
        sys.stderr.write(f"anipy-cli: fatal error: {error}, exiting\n")
        sys.exit(1)

def get_configured_player(player_override: Optional[str] = None, rpc_client=None) -> "PlayerBase":
    config = Config()
    player = Path(player_override or config.player_path)

    if "mpv" in player.stem:
        args = config.mpv_commandline_options
    elif "vlc" in player.stem:
        args = config.vlc_commandline_options
    else: 
        args = []

    return get_player(player, args, rpc_client)
