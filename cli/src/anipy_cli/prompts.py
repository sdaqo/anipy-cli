import time
from typing import TYPE_CHECKING, Optional, List, Tuple
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from anipy_api.provider import (
    BaseProvider,
    FilterCapabilities,
    Filters,
    LanguageTypeEnum,
    Season,
)
from anipy_api.anime import Anime

from anipy_cli.util import (
    DotSpinner,
    get_anime_season,
    get_prefered_providers,
    error,
    parse_episode_ranges,
    convert_letter_to_season,
)
from anipy_cli.colors import colors
from anipy_cli.config import Config


if TYPE_CHECKING:
    from anipy_api.provider import Episode


def search_show_prompt(
    mode: str, skip_season_search: bool = False
) -> Optional["Anime"]:
    if not (Config().skip_season_search or skip_season_search):
        anime = season_search_pre_prompt(mode)
        if anime is not None:
            return anime

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

    if len(results) == 0:
        error("no search results")
        # Do not prompt for season again
        return search_show_prompt(mode, skip_season_search=True)

    anime = inquirer.fuzzy(  # type: ignore
        message="Select Show:",
        choices=[
            Choice(value=r, name=f"{n + 1}. {repr(r)}") for n, r in enumerate(results)
        ],
        long_instruction=(
            "\nS = Anime is available in sub\n"
            "D = Anime is available in dub\n"
            "First two letters indicate the provider\n"
            "To skip this prompt press ctrl+z"
        ),
        mandatory=False,
    ).execute()

    return anime


def _get_season_provider(mode: str) -> Optional["BaseProvider"]:
    season_provider = None
    for p in get_prefered_providers(mode):
        if p.FILTER_CAPS & (
            FilterCapabilities.SEASON
            | FilterCapabilities.YEAR
            | FilterCapabilities.NO_QUERY
        ):
            season_provider = p
    return season_provider


def season_search_pre_prompt(
    mode: str, year: Optional[int] = None, season: Optional[str] = None
) -> Optional["Anime"]:
    season_provider = _get_season_provider(mode)
    assume_season_search = Config().assume_season_search

    # If there is no proper season provider
    if season_provider is None:
        if not assume_season_search:
            return
        # If assume search was on, and there is no proper season provider
        print(
            f"`assume_season_search` was set to true, but the providers ({', '.join(Config().providers[mode])}) you have selected do not have seasonal capabilities"
        )
        return

    if assume_season_search or (year and season):
        return season_search_prompt(season_provider, year, season)

    should_search = inquirer.confirm("Do you want to search in season?", default=False).execute()  # type: ignore

    if should_search:
        return season_search_prompt(season_provider)

    print(
        "Hint: you can set `skip_season_search` to `true` in the config to skip this prompt!"
    )


def season_search_prompt(
    provider: "BaseProvider", year: Optional[int] = None, season: Optional[str] = None
) -> Optional["Anime"]:
    if year is None:
        curr_year = time.localtime().tm_year
        year = inquirer.number(  # type: ignore
            message="Enter year:",
            long_instruction="To skip this prompt press ctrl+z",
            default=curr_year,
            mandatory=False,
        ).execute()

    if year is None:
        return

    if season is None:
        season = inquirer.select(  # type: ignore
            message="Select Season:",
            choices=["Winter", "Spring", "Summer", "Fall"],
            instruction="The season selected by default is the current season.",
            long_instruction="To skip this prompt press ctrl+z",
            default=get_anime_season(time.localtime().tm_mon),
            mandatory=False,
        ).execute()

    if season is None:
        return

    discovered_anime = get_anime_by_season(provider, year, Season[season.upper()])

    if not discovered_anime:
        error(f"No anime found in {season} {year}")
        return

    anime = inquirer.fuzzy(  # type: ignore
        message="Select Show:",
        choices=[
            Choice(value=r, name=f"{n + 1}. {repr(r)}")
            for n, r in enumerate(discovered_anime)
        ],
        long_instruction=(
            "\nS = Anime is available in sub\n"
            "D = Anime is available in dub\n"
            "First two letters indicate the provider\n"
            "To skip this prompt press ctrl+z"
        ),
        mandatory=False,
    ).execute()

    return anime


def get_anime_by_season(provider: "BaseProvider", year: int, season: Season):
    with DotSpinner(
        "Retrieving anime in ", colors.BLUE, f"{season.name} {year}", "..."
    ):
        filters = Filters(year=year, season=season)
        return [
            Anime.from_search_result(provider, r)
            for r in provider.get_search(query="", filters=filters)
        ]


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


def parse_seasonal_search(mode: str, passed: str | bool) -> Optional["Anime"]:
    """
    Takes the mode we are in, as well as the search parameters.
    Asks the user to choose an anime.

    `Mode`: The provider to use.
    `Passed`: The search terms passed (ex: `year:season`) or True,
    if True we'll ask the user for this information
    """
    if isinstance(passed, bool):
        if not passed:
            return

        provider = _get_season_provider(mode)

        if not provider:
            error(
                "No valid provider was found for season search in the current mode",
                fatal=True,
            )

        return season_search_prompt(provider)

    options = iter(passed.split(":"))
    year = next(options, None)
    season = next(options, None)

    if (not year) or not year.isnumeric():
        error("A year was either not provided, or was not a number", fatal=True)

    if not season:
        error("A season was not provided", fatal=True)

    season = convert_letter_to_season(season)

    if not season:
        error("The given season was not a valid season", fatal=True)

    return season_search_pre_prompt(mode, int(year), season)


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
