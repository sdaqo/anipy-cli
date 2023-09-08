import os
import yaml
import functools
from pathlib import Path
from sys import platform
from sys import exit as sys_exit


class SysNotFoundError(Exception):
    pass


class Config:
    def __init__(self):
        self._config_file, self._yaml_conf = Config._read_config()

        if not self._yaml_conf:
            self._yaml_conf = {}
            self._create_config()  # Create config file

    @property
    def _anipy_cli_folder(self):
        return Path(Path(__file__).parent)

    @property
    def download_folder_path(self):
        return self._get_path_value(
            "download_folder_path", self._anipy_cli_folder / "download"
        )

    @property
    def seasonals_dl_path(self):
        return self._get_path_value(
            "seasonals_dl_path", self.download_folder_path / "seasonals"
        )

    @property
    def user_files_path(self):
        return self._get_path_value(
            "user_files_path", self._anipy_cli_folder / "user_files"
        )

    @property
    def history_file_path(self):
        return self.user_files_path / "history.json"

    @property
    def seasonal_file_path(self):
        return self.user_files_path / "seasonals.json"

    @property
    def gogoanime_url(self):
        return self._get_value("gogoanime_url", "https://gogoanime.gg/", str)

    @property
    def player_path(self):
        return self._get_value("player_path", "mpv", str)

    @property
    def mpv_commandline_options(self):
        return self._get_value("mpv_commandline_options", ["--keep-open=no"], list)

    @property
    def vlc_commandline_options(self):
        return self._get_value("vlc_commandline_options", [], list)

    @property
    def reuse_mpv_window(self):
        return self._get_value("reuse_mpv_window", False, bool)

    @property
    def ffmpeg_hls(self):
        return self._get_value("ffmpeg_hls", False, bool)

    @property
    def ffmpeg_log_path(self):
        return self.user_files_path / "ffmpeg_log"

    @property
    def download_name_format(self):
        return self._get_value(
            "download_name_format", "{show_name}_{episode_number}.mp4", str
        )

    @property
    def download_remove_dub_from_folder_name(self):
        return self._get_value("download_remove_dub_from_folder_name", False, bool)

    @property
    def dc_presence(self):
        return self._get_value("dc_presence", False, bool)

    @property
    def auto_open_dl_defaultcli(self):
        return self._get_value("auto_open_dl_defaultcli", False, bool)

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
        try:
            self._get_config_path().mkdir(exist_ok=True, parents=True)
            config_options = {}
            # generate config based on attrs and default values of config class
            for attribute, value in Config.__dict__.items():
                if attribute.startswith("_"):
                    continue

                if isinstance(value, property):
                    val = self.__getattribute__(attribute)
                    config_options[attribute] = (
                        str(val) if isinstance(val, Path) else val
                    )
            self._config_file.touch()
            with open(self._config_file, "w") as file:
                yaml.dump(
                    yaml.dump(config_options, file, indent=4, default_flow_style=False)
                )
        except PermissionError as e:
            print(f"Failed to create config file: {repr(e)}")
            sys_exit(1)

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
        linux_path = Path().home() / ".config" / "anipy-cli"
        windows_path = Path().home() / "AppData" / "Local" / "anipy-cli"
        macos_path = Path().home() / ".config" / "anipy-cli"

        if platform == "linux":
            return linux_path
        elif platform == "darwin":
            return macos_path
        elif platform == "win32":
            return windows_path
        else:
            raise SysNotFoundError(platform)
