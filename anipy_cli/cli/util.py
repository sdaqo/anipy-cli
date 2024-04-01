from InquirerPy.base.simple import BaseSimplePrompt
from InquirerPy.prompts.input import InputPrompt
from InquirerPy.utils import get_style
from yaspin.core import Yaspin
from yaspin.spinners import Spinners
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List, Optional, List
from InquirerPy import inquirer

from anipy_cli.colors import cprint, colors, cinput, color
from anipy_cli.misc import Entry, search_in_season_on_gogo, print_names, error
from anipy_cli.url_handler import epHandler, videourl
from anipy_cli.config import Config
from anipy_cli.mal import MAL
from anipy_cli.player import PlayerBase
from anipy_cli.provider import list_providers, Episode, BaseProvider
from anipy_cli.anime import Anime

def binge(ep_list, quality, player: PlayerBase, mode="", mal_class: MAL = None):
    """
    TODO: bruh what is this, let this accept a list of Entry
    Accepts ep_list like so:
        {"name" {'ep_urls': [], 'eps': [], 'category_url': }, "next_anime"...}
    """
    cprint(colors.RED, "To quit press CTRL+C")
    try:
        for i in ep_list:
            print(i)
            show_entry = Entry()
            show_entry.show_name = i
            show_entry.category_url = ep_list[i]["category_url"]
            show_entry.latest_ep = epHandler(show_entry).get_latest()
            for url, ep in zip(ep_list[i]["ep_urls"], ep_list[i]["eps"]):
                show_entry.ep = ep
                show_entry.embed_url = ""
                show_entry.ep_url = url
                cprint(
                    colors.GREEN,
                    "Fetching links for: ",
                    colors.END,
                    show_entry.show_name,
                    colors.RED,
                    f""" | EP: {
                    show_entry.ep
                    }/{
                    show_entry.latest_ep
                    }""",
                )

                url_class = videourl(show_entry, quality)
                url_class.stream_url()
                show_entry = url_class.get_entry()
                player.play_title(show_entry)
                player.wait()

                if mode == "seasonal":
                    Seasonal().update_show(
                        show_entry.show_name, show_entry.category_url, show_entry.ep
                    )
                elif mode == "mal":
                    mal_class.update_watched(show_entry.show_name, show_entry.ep)

    except KeyboardInterrupt:
        player.kill_player()


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
            anime_in_season = MAL().get_seasonal_anime(season_year, season_name)

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


class DotSpinner:
    def __init__(self, *text_and_colors):
        self.spinner = Yaspin(
            text=color(*text_and_colors), color="cyan", spinner=Spinners.dots
        )

    def __enter__(self):
        self.spinner.__enter__()
        return self.spinner

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.spinner.__exit__(exc_type, exc_val, exc_tb)


def search_show_prompt(loop_on_nores: bool = True) -> Optional[Anime]:
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

    if loop_on_nores:
        if len(results) == 0:
            error("no search results")
            search_show_prompt()

    anime = inquirer.fuzzy(
        message="Select Show:",
        choices=results,
        long_instruction="To skip this prompt press ctrl+z",
        mandatory=False,
    ).execute()

    return anime


def pick_episode_prompt(anime: Anime, instruction: str = "") -> Optional[Episode]:
    with DotSpinner("Fetching episode list for ", colors.BLUE, anime.name, "..."):
        episodes = anime.get_episodes()

    return inquirer.fuzzy(
        message="Select Episode:",
        instruction=instruction,
        choices=episodes,
        long_instruction="To skip this prompt press ctrl+z",
        mandatory=False,
    ).execute()


def pick_episode_range_prompt(anime: Anime) -> List[Episode]:
    with DotSpinner("Fetching episode list for ", colors.BLUE, anime.name, "..."):
        episodes = anime.get_episodes()

    res = inquirer.fuzzy(
        message="Select Episode Range:",
        choices=episodes,
        multiselect=True,
        validate=lambda res: len(res) == 2,
        instruction="Use ctrl+space to select two episodes and press enter to continue",
        long_instruction="To skip this prompt press ctrl+z",
        invalid_message="Select two episodes!",
        mandatory=False,
        keybindings={"toggle": [{"key": "c-space"}]},
        transformer=lambda res: f"{res[0]} -> {res[1]}",
    ).execute()

    return episodes[episodes.index(res[0]) : episodes.index(res[1]) + 1]


def get_prefered_providers() -> Iterator[BaseProvider]:
    preferred_providers = Config().providers

    for i in list_providers():
        if i.NAME in preferred_providers:
            yield i()
