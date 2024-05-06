from typing import TYPE_CHECKING, Optional, List, Tuple
from InquirerPy import inquirer
from anipy_api.provider import LanguageTypeEnum
from anipy_api.anime import Anime

from anipy_cli.util import (
    DotSpinner,
    get_prefered_providers,
    error,
    parse_episode_ranges,
)
from anipy_cli.colors import colors
from anipy_cli.config import Config


if TYPE_CHECKING:
    from anipy_api.provider import Episode


def search_show_prompt(mode: str) -> Optional["Anime"]:
    query = inquirer.text(  # type: ignore
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

    anime = inquirer.fuzzy(  # type: ignore
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

    return inquirer.fuzzy(  # type: ignore
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

    res = inquirer.text(  # type: ignore
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
        res = inquirer.confirm("Want to watch in dub?").execute()  # type: ignore
        print("Hint: you can set a default in the config with `preferred_type`!")

        if res:
            return LanguageTypeEnum.DUB
        else:
            return LanguageTypeEnum.SUB
    else:
        return next(iter(anime.languages))


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
