from typing import TYPE_CHECKING, Optional, List

from anipy_cli.download_component import DownloadComponent

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.colors import colors, cprint
from anipy_cli.config import Config
from anipy_cli.prompts import (
    parse_seasonal_search,
    pick_episode_range_prompt,
    search_show_prompt,
    lang_prompt,
    parse_auto_search,
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

    def _get_anime_from_user(self):
        if (ss := self.options.seasonal_search) is not None:
            return parse_seasonal_search(
                "download",
                ss,
            )

        return search_show_prompt("download")

    def take_input(self):
        if self.options.search is not None:
            self.anime, self.lang, self.episodes = parse_auto_search(
                "download", self.options.search
            )
            return

        anime = self._get_anime_from_user()

        if anime is None:
            return False

        self.lang = lang_prompt(anime)

        episodes = pick_episode_range_prompt(anime, self.lang)

        self.anime = anime
        self.episodes = episodes

    def process(self):
        assert self.episodes is not None
        assert self.anime is not None
        assert self.lang is not None

        errors = DownloadComponent(self.options, self.dl_path).download_anime(
            [(self.anime, self.lang, self.episodes)], only_skip_ep_on_err=True
        )
        DownloadComponent.serve_download_errors(errors, only_skip_ep_on_err=True)

    def show(self):
        pass

    def post(self):
        pass
