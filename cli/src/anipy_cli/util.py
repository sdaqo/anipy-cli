import functools
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List, Optional, Tuple

from anipy_api.anime import Anime
from anipy_api.download import Downloader
from anipy_api.player import get_player
from anipy_api.provider import LanguageTypeEnum, list_providers, get_provider
from anipy_api.locallist import LocalList, LocalListData, LocalListEntry
from anipy_api.error import LangTypeNotAvailableError
from InquirerPy import inquirer
from yaspin.core import Yaspin
from yaspin.spinners import Spinners

from anipy_cli.colors import cinput, color, colors, cprint
from anipy_cli.config import Config
from anipy_cli.discord import DiscordPresence

if TYPE_CHECKING:
    from anipy_api.player import PlayerBase
    from anipy_api.provider import BaseProvider, Episode, ProviderStream


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


def search_show_prompt(mode: str) -> Optional["Anime"]:
    query = inquirer.text(
        "Search Anime:",
        long_instruction="To cancel this prompt press ctrl+z",
        mandatory=False,
    ).execute()

    if query is None:
        return None

    with DotSpinner("Searching for ", colors.BLUE, query, "..."):
        results: List[Anime] = []
        for provider in get_prefered_providers(mode):
            results.extend(
                [
                    Anime.from_search_result(provider, x)
                    for x in provider.get_search(query)
                ]
            )

    print(mode)
    if len(results) == 0:
        error("no search results")
        return search_show_prompt(mode)

    anime = inquirer.fuzzy(
        message="Select Show:",
        choices=results,
        long_instruction="\nS = Anime is available in sub\nD = Anime is available in dub\nTo skip this prompt press ctrl+z",
        mandatory=False,
    ).execute()

    return anime


def pick_episode_prompt(
    anime: "Anime", lang: LanguageTypeEnum, instruction: str = ""
) -> Optional["Episode"]:
    with DotSpinner("Fetching episode list for ", colors.BLUE, anime.name, "..."):
        episodes = anime.get_episodes(lang)

    if not episodes:
        error(f"No episodes available for {anime.name}")
        return None

    return inquirer.fuzzy(
        message="Select Episode:",
        instruction=instruction,
        choices=episodes,
        long_instruction="To skip this prompt press ctrl+z",
        mandatory=False,
    ).execute()


def pick_episode_range_prompt(
    anime: "Anime", lang: LanguageTypeEnum
) -> List["Episode"]:
    with DotSpinner("Fetching episode list for ", colors.BLUE, anime.name, "..."):
        episodes = anime.get_episodes(lang)

    if not episodes:
        error(f"No episodes available for {anime.name}")
        return []

    res = inquirer.text(
        message=f"Input Episode Range(s) from episodes {episodes[0]} to {episodes[-1]}:",
        long_instruction="Type e.g. `1-10 19-20` or `3-4` or `3`\nTo skip this prompt press ctrl+z",
        mandatory=False,
    ).execute()

    if res is None:
        return []

    return parse_episode_ranges(res, episodes)


def lang_prompt(anime: "Anime") -> LanguageTypeEnum:
    config = Config()
    preferred = (
        LanguageTypeEnum[config.preferred_type.upper()]
        if config.preferred_type is not None
        else None
    )

    if preferred in anime.languages:
        return preferred

    if LanguageTypeEnum.DUB not in anime.languages:
        return LanguageTypeEnum.SUB

    if len(anime.languages) == 2:
        res = inquirer.confirm("Want to watch in dub?").execute()
        print("Hint: you can set a default in the config with `preferred_type`!")

        if res:
            return LanguageTypeEnum.DUB
        else:
            return LanguageTypeEnum.SUB
    else:
        return next(iter(anime.languages))

def get_prefered_providers(mode: str) -> Iterator["BaseProvider"]:
    config = Config()
    preferred_providers = config.providers[mode]

    if not preferred_providers:
        error(
            f"you have no providers set for {mode} mode, look into your config",
            fatal=True,
        )

    for i in list_providers():
        if i.NAME in preferred_providers:
            url_override = config.provider_urls.get(i.NAME, None)
            yield i(url_override)


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
        type=stream.language,
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
        
        try:
            picked = picked | set(
                episodes[
                    episodes.index(parsenum(numbers[0])) : episodes.index(
                        parsenum(numbers[-1])
                    )
                    + 1
                ]
            )
        except ValueError:
            error(f"range `{r}` is not contained in episodes {episodes}")
            continue

    return sorted(picked)


def parse_auto_search(
    mode: str, passed: str
) -> Tuple["Anime", LanguageTypeEnum, List["Episode"]]:
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
        for provider in get_prefered_providers(mode):
            results.extend(
                [
                    Anime.from_search_result(provider, x)
                    for x in provider.get_search(query)
                ]
            )
    if len(results) == 0:
        error(f"no anime found for query {query}", fatal=True)
    
    result = results[0]
    if ltype is None:
        lang = lang_prompt(result)
    else:
        lang = LanguageTypeEnum[ltype.upper()]

    if lang not in result.languages:
        error(f"{lang} is not available for {result.name}", fatal=True)

    episodes = result.get_episodes(lang)
    chosen = parse_episode_ranges(ranges, episodes)
    if not chosen:
        error("could not determine any epiosdes from search parameter", fatal=True)

    return result, lang, chosen


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
        sys.stderr.write(color(colors.RED, f"anipy-cli: error: ", colors.END, f"{error}\n"))
    else:
        sys.stderr.write(color(colors.RED, "anipy-cli: fatal error: ", colors.END, f"{error}, exiting\n"))
        sys.exit(1)


def get_configured_player(player_override: Optional[str] = None) -> "PlayerBase":
    config = Config()
    player = Path(player_override or config.player_path)
    if config.dc_presence:
        discord_cb = DiscordPresence.instance().dc_presence_callback
    else:
        discord_cb = None

    if "mpv" in player.stem:
        args = config.mpv_commandline_options
    elif "vlc" in player.stem:
        args = config.vlc_commandline_options
    else:
        args = []

    return get_player(player, args, discord_cb)



def migrate_locallist(file):
    import json
    import re
    
    error(f"{file} is in an unsuported format, trying to migrate the old gogoanime entries...")

    old_data = json.load(file.open("r"))
    new_list = LocalListData({})
    gogo = get_provider(
        "gogoanime", base_url_override=Config().provider_urls.get("gogoanime", None)
    )
    assert gogo is not None

    try:
        for k, v in old_data.items():
            name = k
            name = re.sub(r"\s?\((dub|japanese\sdub)\)", "", name, flags=re.IGNORECASE)
            identifier = Path(v.get("category_url", v["category-link"])).name
            is_dub = identifier.endswith("-dub") or identifier.endswith("-japanese-dub")
            identifier = identifier.removesuffix("-dub").removesuffix("-japanese-dub")
            episode = v["ep"]
            unique_id = f"gogoanime:{identifier}"
            
            langs = set()

            try:
                gogo.get_episodes(identifier, lang=LanguageTypeEnum.DUB)
                langs.add(LanguageTypeEnum.DUB)
                gogo.get_episodes(identifier, lang=LanguageTypeEnum.SUB)
                langs.add(LanguageTypeEnum.SUB)
            except LangTypeNotAvailableError:
                pass

            if not langs:
                error(f"> failed to migrate {name}, as it was not found in gogoanime")

            if is_dub and LanguageTypeEnum.DUB not in langs:
                error(
                    f"> failed to migrate {name}, as it was configured as dub but"
                    f"{gogo.BASE_URL}/category/{identifier}-dub or {gogo.BASE_URL}/category/{identifier}-japanese-dub was not found!"
                )
                continue


            new_entry = LocalListEntry(
                provider="gogoanmie",
                name=name,
                identifier=identifier,
                episode=episode,
                language=LanguageTypeEnum.DUB if is_dub else LanguageTypeEnum.SUB,
                languages=langs,
                timestamp=int(time.time())
            )

            new_list.data[unique_id] = new_entry

        new_list.write(file)
        return new_list
    except KeyError:
        choice = inquirer.confirm(
            message=f"Can not migrate {file}, should it be delted?",
            default=False,
        ).execute()
        if choice:
            file.unlink()
            return new_list
        else:
            error("could not read {file}", fatal=True)
