import functools
import inspect
import os
from pathlib import Path
from sys import platform
from string import Template
from appdirs import user_data_dir, user_config_dir

import yaml

from anipy_cli.version import __version__, __appname__


class Config:
    def __init__(self):
        self._config_file, self._yaml_conf = Config._read_config()

        if not self._yaml_conf:
            self._yaml_conf = {}
            self._create_config()  # Create config file

    @property
    def user_files_path(self):
        """
        Path to user files, this includes history, seasonals files and more.
        You may use `~` or environment vars in your path.
        """
        
        return self._get_path_value(
            "user_files_path", Path(user_data_dir(__appname__, appauthor=False))
        )

    @property
    def download_folder_path(self):
        """
        Path to your download folder/directory.
        You may use `~` or environment vars in your path.
        """
        return self._get_path_value(
            "download_folder_path", self.user_files_path / "download"
        )

    @property
    def seasonals_dl_path(self):
        """
        Path to your seasonal downloads directory.
        You may use `~` or environment vars in your path.
        """
        return self._get_path_value(
            "seasonals_dl_path", self.download_folder_path / "seasonals"
        )

    @property
    def _history_file_path(self):
        return self.user_files_path / "history.json"

    @property
    def _seasonal_file_path(self):
        return self.user_files_path / "seasonals.json"

    @property
    def providers(self):
        """
        List of providers that will be used to look up anime.
        For a updated list of providers look here:

        Supported providers (as of $version): gogoanime

        Examples:
            providers: ["provider1", "provider2"]
        """
        return self._get_value("providers", ["gogoanime"], list)

    @property
    def player_path(self):
        """
        Path to your video player.
        For a list of supported players look here:

        Supported players (as of $version): mpv, vlc, syncplay, mpvnet

        Examples:
            player_path: /usr/bin/syncplay # full path
            player_path: syncplay # if in PATH this also works
            player_path: C:\\\\Programms\\mpv\\mpv.exe # on windows path with .exe
        """
        return self._get_path_value("player_path", Path("mpv"))

    @property
    def mpv_commandline_options(self):
        """
        Extra commandline arguments for mpv and derivative.

        Examples:
            mpv_commandline_options: ["--keep-open=no", "--fs=yes"]
        """
        return self._get_value("mpv_commandline_options", ["--keep-open=no"], list)

    @property
    def vlc_commandline_options(self):
        """
        Extra commandline arguments for vlc.

        Examples:
            vlc_commandline_options: ["--fullscreen"]
        """
        return self._get_value("vlc_commandline_options", [], list)

    @property
    def reuse_mpv_window(self):
        """
        Reuse the mpv window instead of closing and reopening.
        This uses python-mpv, which uses libmpv, on linux this is (normally) preinstalled
        with mpv, on windows you have to get the mpv-2.dll file from here:
        https://sourceforge.net/projects/mpv-player-windows/files/libmpv/
        """
        return self._get_value("reuse_mpv_window", False, bool)

    @property
    def ffmpeg_hls(self):
        """
        Always use ffmpeg to download m3u8 playlists instead of the internal downloader.
        To temporarily enable this use the `--ffmpeg` command line flag.
        """
        return self._get_value("ffmpeg_hls", False, bool)

    @property
    def remux_to(self):
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
    def download_name_format(self):
        """
        Specify the name format of a download, available fields are:
            show_name: name of the show/anime
            episode_number: number of the episode
            quality: quality/resolution of the video
            provider: provider used to download

        The fields should be set in curly braces i.e. `{field_name}`.
        Do not add a suffix (e.g. '.mp4') here, if you want to change this
        look at the `remux_to` config option.

        Examples:
            download_name_format: "[{provider}] {show_name}E{episode_number} [{quality}p]"
            download_name_format: "{show_name}_{episode_number}"

        """

        # Remove suffix for past 3.0.0 versions
        value = self._get_value(
            "download_name_format", "{show_name}_{episode_number}", str
        )
        return Path(value).with_suffix("").__str__()

    @property
    def download_remove_dub_from_folder_name(self):
        """
        Remove `(dub)` from folder names.
        """
        return self._get_value("download_remove_dub_from_folder_name", False, bool)

    @property
    def dc_presence(self):
        """
        Activate discord presence, only works with discord open.
        """
        return self._get_value("dc_presence", False, bool)

    @property
    def auto_open_dl_defaultcli(self):
        """
        This automatically opens the downloaded file if downloaded through the
        `d` option in the default cli.
        """
        return self._get_value("auto_open_dl_defaultcli", True, bool)

    @property
    def mal_local_user_list_path(self):
        return self.user_files_path / "mal_list.json"

    @property
    def mal_user(self):
        return self._get_value("mal_user", "", str)

    @property
    def mal_password(self):
        return self._get_value("mal_password", "", str)

    @property
    def auto_sync_mal_to_seasonals(self):
        return self._get_value("auto_sync_mal_to_seasonals", False, bool)

    @property
    def auto_map_mal_to_gogo(self):
        return self._get_value("auto_map_mal_to_gogo", False, bool)

    @property
    def mal_status_categories(self):
        return self._get_value("mal_status_categories", list(["watching"]), list)

    @property
    def anime_types(self):
        """
        Specify which anime types (dub or sub) are shown in search results.

        Examples:
            anime_types: ["sub"] # only sub
            anime_types: ["sub", "dub"] # both sub and dub
        """
        return self._get_value("anime_types", list(["sub", "dub"]), list)

    def _get_path_value(self, key: str, fallback: Path) -> Path:
        path = self._get_value(key, fallback, str)
        try:
            # os.path.expanduser is equivalent to Path().expanduser()
            # But because pathlib doesn't have expandvars(), we resort
            # to using the os module inside the Path constructor
            return Path(os.path.expandvars(path)).expanduser()
        except:
            return fallback

    def _get_value(self, key: str, fallback, typ: object):
        value = self._yaml_conf.get(key, fallback)
        if isinstance(value, typ):
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

            if isinstance(value, property):
                doc = inspect.getdoc(value)
                if doc:
                    # Add docstrings
                    doc = Template(doc).safe_substitute(version=__version__)
                    doc = "\n".join([f"# {l}" for l in doc.split("\n")])
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
    def _read_config():
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

