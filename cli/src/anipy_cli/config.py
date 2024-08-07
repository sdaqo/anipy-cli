import functools
import inspect
import os
from pathlib import Path
from string import Template
from typing import Any, Dict, List, Optional, Tuple, Type

import yaml
from appdirs import user_config_dir, user_data_dir

from anipy_cli import __appname__, __version__


class Config:
    def __init__(self):
        self._config_file, self._yaml_conf = Config._read_config()

        if not self._yaml_conf:
            self._yaml_conf = {}
            self._create_config()  # Create config file

    @property
    def user_files_path(self) -> Path:
        """Path to user files, this includes history, seasonals files and more.

        You may use `~` or environment vars in your path.
        """

        return self._get_path_value(
            "user_files_path", Path(user_data_dir(__appname__, appauthor=False))
        )

    @property
    def _history_file_path(self) -> Path:
        return self.user_files_path / "history.json"

    @property
    def _seasonal_file_path(self) -> Path:
        return self.user_files_path / "seasonals.json"

    @property
    def _mal_local_user_list_path(self) -> Path:
        return self.user_files_path / "mal_list.json"

    @property
    def download_folder_path(self) -> Path:
        """Path to your download folder/directory.

        You may use `~` or environment vars in your path.
        """
        return self._get_path_value(
            "download_folder_path", self.user_files_path / "download"
        )

    @property
    def seasonals_dl_path(self) -> Path:
        """Path to your seasonal downloads directory.

        You may use `~` or environment vars in your path.
        """
        return self._get_path_value(
            "seasonals_dl_path", self.download_folder_path / "seasonals"
        )

    @property
    def providers(self) -> Dict[str, List[str]]:
        """A list of pairs defining which providers will search for anime
        in different parts of the program. Configurable areas are as follows:
        default (and history), download (-D), seasonal (-S), binge (-B) and mal
        (-M) The example will show you how it is done! Please note that for seasonal
        search always the first provider that supports it is used.

        For an updated list of providers look here: https://sdaqo.github.io/anipy-cli/availabilty

        Supported providers (as of $version): gogoanime, yugenanime

        Examples:
            providers:
                default: ["provider1"] # used in default mode and for the history
                download: ["provider2"]
                seasonal: ["provider3"]
                binge: ["provider4"]
                mal: ["provider2", "provider3"]
        """
        defaults = {
            "default": ["yugenanime"],
            "download": ["yugenanime"],
            "history": ["yugenanime"],
            "seasonal": ["yugenanime"],
            "binge": ["yugenanime"],
            "mal": ["yugenanime"],
        }

        value = self._get_value("providers", defaults, dict)

        # Merge Dicts
        defaults.update(value)
        return defaults

    @property
    def provider_urls(self) -> Dict[str, str]:
        """A list of pairs to override the default urls that providers use.

        Examples:
            provider_urls:
              gogoanime: "https://gogoanime3.co"
            provider_urls: {} # do not override any urls
        """

        return self._get_value("provider_urls", {}, dict)

    @property
    def player_path(self) -> Path:
        """
        Path to your video player.
        For a list of supported players look here: https://sdaqo.github.io/anipy-cli/availabilty

        Supported players (as of $version): mpv, vlc, syncplay, mpvnet, mpv-controlled

        Info for mpv-controlled:
        Reuse the mpv window instead of closing and reopening.
        This uses python-mpv, which uses libmpv, on linux this is (normally) preinstalled
        with mpv, on windows you have to get the mpv-2.dll file from here:
        https://sourceforge.net/projects/mpv-player-windows/files/libmpv/

        Examples:
            player_path: /usr/bin/syncplay # full path
            player_path: syncplay # if in PATH this also works
            player_path: C:\\\\Programms\\mpv\\mpv.exe # on windows path with .exe
            player_path: mpv-controlled # recycle your mpv windows!
        """
        return self._get_path_value("player_path", Path("mpv"))

    @property
    def mpv_commandline_options(self) -> List[str]:
        """Extra commandline arguments for mpv and derivative.

        Examples:
            mpv_commandline_options: ["--keep-open=no", "--fs=yes"]
        """
        return self._get_value("mpv_commandline_options", ["--keep-open=no"], list)

    @property
    def vlc_commandline_options(self) -> List[str]:
        """Extra commandline arguments for vlc.

        Examples:
            vlc_commandline_options: ["--fullscreen"]
        """
        return self._get_value("vlc_commandline_options", [], list)

    @property
    def iina_commandline_options(self) -> List[str]:
        """Extra commandline arguments for iina.

        Examples:
            iina_commandline_options: ["--mpv-fullscreen"]
        """
        return self._get_value("iina_commandline_options", [], list)

    @property
    def reuse_mpv_window(self) -> bool:
        """DEPRECATED This option was deprecated in 3.0.0, please use `mpv-
        controlled` in the `player_path` instead!

        Reuse the mpv window instead of closing and reopening. This uses
        python-mpv, which uses libmpv, on linux this is (normally)
        preinstalled with mpv, on windows you have to get the mpv-2.dll
        file from here:
        https://sourceforge.net/projects/mpv-player-windows/files/libmpv/
        """
        return self._get_value("reuse_mpv_window", False, bool)

    @property
    def ffmpeg_hls(self) -> bool:
        """Always use ffmpeg to download m3u8 playlists instead of the internal
        downloader.

        To temporarily enable this use the `--ffmpeg` command line flag.
        """
        return self._get_value("ffmpeg_hls", False, bool)

    @property
    def remux_to(self) -> Optional[str]:
        """
        Remux resulting download to a specific container using ffmpeg.
        You can use about any conatainer supported by ffmpeg: `.your-container`.

        Examples:
            remux_to: .mkv # remux all downloads to .mkv container
            remux_to .mp4 # downloads with ffmpeg default to a .mp4 container,
            with this option the internal downloader's downloads also get remuxed
            remux_to: null or remux_to: "" # do not remux
        """
        return self._get_value("remux_to", None, str)

    @property
    def download_name_format(self) -> str:
        """
        Specify the name format of a download, available fields are:
            show_name: name of the show/anime
            episode_number: number of the episode
            quality: quality/resolution of the video
            provider: provider used to download
            type: this field is populated with `dub` if the episode is in dub format or `sub` otherwise

        The fields should be set in curly braces i.e. `{field_name}`.
        Do not add a suffix (e.g. '.mp4') here, if you want to change this
        look at the `remux_to` config option.

        You have to at least use episode_number in the format or else, while downloading,
        perceding episodes of the same series will be skipped because the file name will be the same.

        Examples:
            download_name_format: "[{provider}] {show_name} E{episode_number} [{type}][{quality}p]"
            download_name_format: "{show_name}_{episode_number}"

        """

        # Remove suffix for past 3.0.0 versions
        value = self._get_value(
            "download_name_format", "{show_name}_{episode_number}", str
        )
        return str(Path(value).with_suffix(""))

    @property
    def dc_presence(self) -> bool:
        """Activate discord presence, only works with discord open."""
        return self._get_value("dc_presence", False, bool)

    @property
    def auto_open_dl_defaultcli(self) -> bool:
        """This automatically opens the downloaded file if downloaded through
        the `d` option in the default cli."""
        return self._get_value("auto_open_dl_defaultcli", True, bool)

    @property
    def mal_user(self) -> str:
        """Your MyAnimeList username for MAL mode."""
        return self._get_value("mal_user", "", str)

    @property
    def mal_password(self) -> str:
        """Your MyAnimeList password for MAL mode.

        The password may also be passed via the `--mal-password <pwd>`
        commandline option.
        """
        return self._get_value("mal_password", "", str)

    @property
    def mal_ignore_tag(self) -> str:
        """All anime in your MyAnimeList with this tag will be ignored by
        anipy-cli.

        Examples:
            mal_ignore_tag: ignore # all anime with ignore tag will be ignored
            mal_ignore_tag: "" # no anime will be ignored
        """
        return self._get_value("mal_ignore_tag", "ignore", str)

    @property
    def mal_dub_tag(self) -> str:
        """All anime in your MyAnimeList with this tag will be switched over to
        dub in MAL mode, if the dub is available. If you do not specify a tag,
        anipy-cli will use `preferred_type` to choose dub or sub in MAL mode.

        Examples:
            mal_dub_tag: dub # all anime with this tag will be switched to dub
            mal_dub_tag: "" # no anime will be switched to dub, except you have preferred_type on dub
        """
        return self._get_value("mal_dub_tag", "dub", str)

    @property
    def mal_tags(self) -> List[str]:
        """Custom tags to tag all anime in your MyAnimeList that are
        altered/added by anipy-cli.

        Examples:
            mal_tags: ["anipy-cli"] # tag all anime with anipy-cli
            mal_tags: ["anipy-cli", "important"] # tag all anime with anipy-cli and important
            mal_tags: null or mal_tags: [] # Do not tag the anime
        """
        return self._get_value("mal_tags", [], list)

    @property
    def mal_status_categories(self) -> List[str]:
        """Status categories of your MyAnimeList that anipy-cli uses for
        downloading/watching new episodes listing anime in your list and stuff
        like that. Normally the watching catagory should be enough as you would
        normally put anime you currently watch in the watching catagory.

        Valid values are: watching, completed, on_hold, dropped, plan_to_watch
        """
        return self._get_value("mal_status_categories", ["watching"], list)

    @property
    def mal_mapping_min_similarity(self) -> float:
        """
        The minumum similarity between titles when mapping anime in MAL mode.
        This is a decimal number from 0 - 1, 1 meaning 100% match and 0 meaning all characters are different.
        If the similarity of a map is below the threshold you will be prompted for a manual map.

        So in summary:
            higher number: more exact matching, but more manual mapping
            lower number: less exact matching, but less manual mapping

        If you are interested, the algorithm being used here is this: https://en.wikipedia.org/wiki/Levenshtein_distance
        """
        return self._get_value("mal_mapping_min_similarity", 0.8, float)

    @property
    def mal_mapping_use_alternatives(self) -> bool:
        """Check alternative names when mapping anime.

        If turned on this will slow down mapping but provide better
        chances of finding a match.
        """
        return self._get_value("mal_mapping_use_alternatives", True, bool)

    @property
    def mal_mapping_use_filters(self) -> bool:
        """Use filters (e.g. year, season etc.) of providers to narrow down the
        results, this will lead to more accurate mapping, but provide wrong
        results if the filters of the provider do not work properly or if anime
        are not correctly marked with the correct data."""
        return self._get_value("mal_mapping_use_filters", True, bool)

    @property
    def auto_sync_mal_to_seasonals(self) -> bool:
        """DEPRECATED This option was deprecated in 3.0.0, please consider
        using the `--mal-sync-seasonals` cli option in compination with `-M`
        instead.

        Automatically sync MyAnimeList to Seasonals list.
        """
        return self._get_value("auto_sync_mal_to_seasonals", False, bool)

    @property
    def auto_map_mal_to_gogo(self) -> bool:
        return self._get_value("auto_map_mal_to_gogo", False, bool)

    @property
    def preferred_type(self) -> Optional[str]:
        """Specify which anime types (dub or sub) you prefer. If this is
        specified, you will not be asked to switch to dub anymore. You can
        however always switch to either in the menu.

        Examples:
            preferred_type: sub
            preferred_type: dub
            preferred_type: null or preferred_type: "" # always ask
        """
        return self._get_value("preferred_type", None, str)

    @property
    def skip_season_search(self) -> bool:
        """If this is set to true you will not be prompted to search in season."""
        return self._get_value("skip_season_search", False, bool)

    @property
    def assume_season_search(self) -> bool:
        """If this is set to true, the system will assume you want to search in season.
        If skip_season_search is true, this will be ignored)"""
        return self._get_value("assume_season_search", False, bool)

    def _get_path_value(self, key: str, fallback: Path) -> Path:
        path = self._get_value(key, fallback, str)
        try:
            # os.path.expanduser is equivalent to Path().expanduser()
            # But because pathlib doesn't have expandvars(), we resort
            # to using the os module inside the Path constructor
            return Path(os.path.expandvars(path)).expanduser()
        except RuntimeError:
            return fallback

    def _get_value(self, key: str, fallback, _type: Type) -> Any:
        value = self._yaml_conf.get(key, fallback)
        if isinstance(value, _type):
            return value

        return fallback

    def _create_config(self):
        self._get_config_path().mkdir(exist_ok=True, parents=True)
        self._config_file.touch()

        dump = ""
        # generate config based on attrs and default values of config class
        for attribute, value in Config.__dict__.items():
            if attribute.startswith("_"):
                continue

            if not isinstance(value, property):
                continue

            doc = inspect.getdoc(value)
            if doc:
                # Add docstrings
                doc = Template(doc).safe_substitute(version=__version__)
                doc = "\n".join([f"# {line}" for line in doc.split("\n")])
                dump = dump + doc + "\n"

            val = self.__getattribute__(attribute)
            val = str(val) if isinstance(val, Path) else val
            dump = (
                dump
                + yaml.dump({attribute: val}, indent=4, default_flow_style=False)
                + "\n"
            )

        self._config_file.write_text(dump)

    @staticmethod
    @functools.lru_cache
    def _read_config() -> Tuple[Path, dict[str, Any]]:
        config_file = Config._get_config_path() / "config.yaml"
        try:
            with config_file.open("r") as conf:
                yaml_conf = yaml.safe_load(conf)
        except FileNotFoundError:
            # There is no config file, create one
            yaml_conf = {}

        return config_file, yaml_conf

    @staticmethod
    def _get_config_path() -> Path:
        return Path(user_config_dir(__appname__, appauthor=False))
