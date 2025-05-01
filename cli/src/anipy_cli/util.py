import sys
import subprocess as sp
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Iterator,
    List,
    Literal,
    NoReturn,
    Optional,
    Union,
    overload,
)

from anipy_api.anime import Anime
from anipy_api.download import Downloader, PostDownloadCallback
from anipy_api.locallist import LocalListData
from anipy_api.player import get_player
from anipy_api.provider import list_providers
from InquirerPy import inquirer
from yaspin.core import Yaspin
from yaspin.spinners import Spinners

from anipy_cli.colors import color, colors
from anipy_cli.config import Config
from anipy_cli.discord import DiscordPresence

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
            color(colors.RED, "anipy-cli: error: ", colors.END, f"{error}\n")
        )
        return

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
            f"you have no providers set for '{mode}' mode, look into your config",
            fatal=True,
        )

    providers = []
    for i in list_providers():
        if i.NAME in preferred_providers:
            url_override = config.provider_urls.get(i.NAME, None)
            providers.append(i(url_override))

    if not providers:
        error(
            f"there are no working providers for '{mode}' mode, look into your config",
            fatal=True,
        )

    for p in providers:
        yield p


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
        episode_number=str(stream.episode).zfill(2),
        quality=stream.resolution,
        provider=anime.provider.NAME,
        type=stream.language,
    )

    filename = Downloader._get_valid_pathname(filename)

    return download_folder / anime_name / filename


def get_post_download_scripts_hook(
    mode: str, anime: "Anime", spinner: DotSpinner
) -> PostDownloadCallback:
    config = Config()
    scripts = config.post_download_scripts[mode]
    timeout = config.post_download_scripts["timeout"]

    def hook(path: Path, stream: "ProviderStream"):
        spinner.hide()
        arguments = [
            str(path),
            anime.name,
            str(stream.episode),
            anime.provider.NAME,
            str(stream.resolution),
            stream.language.name,
        ]
        for s in scripts:
            sub_proc = sp.Popen([s, *arguments])
            sub_proc.wait(timeout)  # type: ignore
        spinner.show()

    return hook


def parse_episode_ranges(ranges: str, episodes: List["Episode"]) -> List["Episode"]:
    picked = set()
    for r in ranges.split():
        numbers = [parsenum(n) for n in r.split("-")]
        if numbers[0] > numbers[-1]:
            error(f"invalid range: {r}")
            continue
        try:
            picked = picked | set(
                episodes[episodes.index(numbers[0]) : episodes.index(numbers[-1]) + 1]
            )
        except ValueError:
            error(f"range `{r}` is not contained in episodes {episodes}")
            continue

    return sorted(picked)


def parsenum(n: str):
    try:
        return int(n)
    except ValueError:
        return float(n)


def find_closest(episodes: List["Episode"], target: "Episode") -> "Episode":
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
        # If the cache size is 0, it means that DiscordPresence was
        # not intialized once in the run_cli function and therefore we
        # can assume that it failed to initialize beacuse of some error.
        if DiscordPresence.cache_info().currsize > 0:
            discord_cb = DiscordPresence().dc_presence_callback
        else:
            discord_cb = None
    else:
        discord_cb = None

    if "mpv" in player.stem:
        args = config.mpv_commandline_options
    elif "vlc" in player.stem:
        args = config.vlc_commandline_options
    elif "iina" in player.stem:
        args = config.iina_commandline_options
    else:
        args = []

    return get_player(player, args, discord_cb)


def get_anime_season(month):
    if 1 <= month <= 3:
        return "Winter"
    elif 4 <= month <= 6:
        return "Spring"
    elif 7 <= month <= 9:
        return "Summer"
    else:
        return "Fall"


def convert_letter_to_season(letter: str) -> Optional[str]:
    """
    Converts the beginning of the name of a season to that season name.

    Ex:
    ```
    win -> Winter
    su -> Summer
    sp -> Spring
    ```

    Returns None if the letter does not correspond to a season
    """
    for season in ["Spring", "Summer", "Fall", "Winter"]:
        if season.startswith(letter.capitalize()):
            return season
    return


def migrate_locallist(file: Path) -> LocalListData:
    error(f"{file} is in an unsuported format...")

    new_list = LocalListData({})
    choice = inquirer.confirm(  # type: ignore
        message="Should it be delted?",
        default=False,
    ).execute()
    if choice:
        file.unlink()
        return new_list
    else:
        error("could not read {file}", fatal=True)
