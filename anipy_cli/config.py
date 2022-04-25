import re
import sys
from pathlib import Path

import yaml




class Config:
    """
    Configuration Class
    """

    # Public fields
    anipy_cli_folder = None
    download_folder_path = None
    seasonals_dl_path = None
    user_files_path = None
    history_file_path = None
    seasonal_file_path = None
    gogoanime_url = None
    mpv_path = None
    mpv_commandline_options = None
    ffmpeg_hls = None
    ffmpeg_log_path = None
    dc_presence = None

    def __init__(self):
        self.anipy_cli_folder = Path(repr(sys.argv[0])).parent / "anipy_cli"

        self.download_folder_path = self.anipy_cli_folder / "download"
        self.seasonals_dl_path = self.download_folder_path / "seasonals"
        self.user_files_path = self.anipy_cli_folder / "user_files"
        self.history_file_path = self.user_files_path / "history.json"
        self.seasonal_file_path = self.user_files_path / "seasonals.json"
        self.gogoanime_url = "https://gogoanime.gg/"

        self.mpv_path = "mpv"

        self.mpv_commandline_options = []
        self.ffmpeg_hls = False

        self.ffmpeg_log_path = self.user_files_path / "ffmpeg_log"

        self.dc_presence = False

        try:
            user_config = yaml.safe_load(open(self.anipy_cli_folder / "config.yaml"))
        except:
            user_config = False

        if user_config:
            regex = re.compile(r"(\s?[^{]*?)\w?(?=\})\s?}}")
            from pprint import pprint
            for key, value in user_config.items():
                match = regex.findall(str(value))
                if match:
                    before = value.split("{{")[0]
                    after = value.split("}}")[1]
                    value = "{}{}{}".format(before, str(self.get(str(match[0]).strip(" "))), after)

                if isinstance(self.get(key), Path):
                    pprint(value)
                    value = Path(value)

                self.__setattr__(key, value)

    def get(self, field):
        return self.__getattribute__(field)



