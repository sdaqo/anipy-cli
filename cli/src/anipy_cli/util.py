import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Iterator, List, Literal, NoReturn, Optional, Tuple, Union, overload

from anipy_api.anime import Anime
from anipy_api.download import Downloader
from anipy_api.player import get_player
from anipy_api.provider import LanguageTypeEnum, list_providers, get_provider
from anipy_api.locallist import LocalListData, LocalListEntry
from anipy_api.error import LangTypeNotAvailableError
from InquirerPy import inquirer
from yaspin.core import Yaspin
from yaspin.spinners import Spinners

from anipy_cli.colors import color, colors
from anipy_cli.config import Config
from anipy_cli.discord import DiscordPresence
from anipy_cli.prompts import lang_prompt

if TYPE_CHECKING:
    from anipy_api.player import PlayerBase
    from anipy_api.provider import BaseProvider, Episode, ProviderStream


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


@overload
def error(error: str, fatal: Literal[True]) -> NoReturn: ...
@overload
def error(error: str, fatal: Literal[False] = ...) -> None: ...

def error(error: str, fatal: bool = False) -> Union[NoReturn, None]:
    if not fatal:
        sys.stderr.write(
            color(colors.RED, f"anipy-cli: error: ", colors.END, f"{error}\n")
        )
    else:
        sys.stderr.write(
            color(
                colors.RED,
                "anipy-cli: fatal error: ",
                colors.END,
                f"{error}, exiting\n",
            )
        )
        sys.exit(1)


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


def migrate_locallist(file: Path) -> LocalListData:
    import json
    import re

    error(
        f"{file} is in an unsuported format, trying to migrate the old gogoanime entries..."
    )

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
                timestamp=int(time.time()),
            )

            new_list.data[unique_id] = new_entry

        new_list.write(file)
        return new_list
    except KeyError:
        choice = inquirer.confirm( # type: ignore
            message=f"Can not migrate {file}, should it be delted?",
            default=False,
        ).execute()
        if choice:
            file.unlink()
            return new_list
        else:
            error("could not read {file}", fatal=True)
