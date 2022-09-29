import yaml
from pathlib import Path
from sys import platform


class SysNotFoundError(Exception):
    pass


class Config:
    def __init__(self):
        self._config_file = self._get_config_path() / "config.yaml"

        try:
            with self._config_file.open("r") as conf:
                self._yaml_conf = yaml.safe_load(conf)
            if self._yaml_conf == None:
                # The config file is empty
                self._yaml_conf = {}
        except FileNotFoundError:
            # There is no config file, create one
            self._yaml_conf = {}
            self._create_config()

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
        return self._get_value("mpv_commandline_options", [], list)

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

    def _get_path_value(self, key: str, fallback: Path) -> Path:
        path = self._get_value(key, fallback, str)
        try:
            return Path(path).expanduser()
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
            (self._get_config_path() / "config.yaml").touch()
        except PermissionError:
            pass

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

       '''
       todo: switch to new config system
       
        # MyAnimeListCredentials
        mal_user = ""
        mal_password = ""

        # sync mal to seasonals file automatically
        auto_sync_mal_to_seasonals = False

        # try mapping MAL entries to gogo_format
        auto_map_mal_to_gogo = False

        # list of status categories that are being considered when binge-watching or downloading
        # possible statuses are:
        # ["watching","completed", "on_hold", "dropped", "plan_to_watch"]
        mal_status_categories = ["watching"]

        # This is relevant for auto mapping MyAnimeList to gogo links
        # - Example Usage -
        # if you don't want dubbed anime, just remove the "dub" entry like so:
        # anime_types = ["sub"]
        anime_types = ["sub", "dub"]
       '''
