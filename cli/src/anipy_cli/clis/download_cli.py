import sys
from typing import TYPE_CHECKING, Optional, List

from anipy_api.download import Downloader

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.colors import colors, cprint
from anipy_cli.config import Config
from anipy_cli.prompts import (
    pick_episode_range_prompt,
    search_show_prompt,
    lang_prompt,
    parse_auto_search,
)
from anipy_cli.util import (
    DotSpinner,
    get_download_path,
)

if TYPE_CHECKING:
    from anipy_api.anime import Anime
    from anipy_api.provider import Episode, LanguageTypeEnum

    from anipy_cli.arg_parser import CliArgs


class DownloadCli(CliBase):
    def __init__(self, options: "CliArgs"):
        super().__init__(options)

        self.anime: Optional["Anime"] = None
        self.episodes: Optional[List["Episode"]] = None
        self.lang: Optional["LanguageTypeEnum"] = None

        self.dl_path = Config().download_folder_path
        if options.location:
            self.dl_path = options.location

    def print_header(self):
        cprint(colors.GREEN, "***Download Mode***")
        cprint(colors.GREEN, "Downloads are stored in: ", colors.END, str(self.dl_path))

    def take_input(self):
        if self.options.search is not None:
            self.anime, self.lang, self.episodes = parse_auto_search(
                "download", self.options.search
            )
            return

        anime = search_show_prompt("download")

        if anime is None:
            sys.exit(0)

        self.lang = lang_prompt(anime)

        episodes = pick_episode_range_prompt(anime, self.lang)

        self.anime = anime
        self.episodes = episodes

    def process(self):
        assert self.episodes is not None
        assert self.anime is not None
        assert self.lang is not None

        config = Config()
        with DotSpinner("Starting Download...") as s:

            def progress_indicator(percentage: float):
                s.set_text(f"Progress: {percentage:.1f}%")

            def info_display(message: str):
                s.write(f"> {message}")

            downloader = Downloader(progress_indicator, info_display)

            for e in self.episodes:
                s.set_text(
                    "Extracting streams for ",
                    colors.BLUE,
                    f"{self.anime.name} ({self.lang})",
                    colors.END,
                    " Episode ",
                    e,
                    "...",
                )

                stream = self.anime.get_video(
                    e, self.lang, preferred_quality=self.options.quality
                )

                info_display(
                    f"Downloading Episode {stream.episode} of {self.anime.name} ({self.lang})"
                )
                s.set_text("Downloading...")

                downloader.download(
                    stream,
                    get_download_path(
                        self.anime, stream, parent_directory=self.dl_path
                    ),
                    container=config.remux_to,
                    ffmpeg=self.options.ffmpeg or config.ffmpeg_hls,
                )

    def show(self):
        pass

    def post(self):
        pass
