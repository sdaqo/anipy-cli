import sys
from typing import TYPE_CHECKING

from anipy_api.locallist import LocalList

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
from anipy_cli.util import DotSpinner, get_configured_player, migrate_locallist

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


class BingeCli(CliBase):
    def __init__(self, options: "CliArgs"):
        super().__init__(options)

        self.player = get_configured_player(self.options.optional_player)
        self.history_list = LocalList(
            Config()._history_file_path, migrate_cb=migrate_locallist
        )

        self.anime = None
        self.episodes = None
        self.lang = None

    def print_header(self):
        cprint(colors.GREEN, "***Binge Mode***")

    def _get_anime_from_user(self):
        if (ss := self.options.seasonal_search) is not None:
            return parse_seasonal_search(
                "binge",
                ss,
            )

        return search_show_prompt("binge")

    def take_input(self):
        if self.options.search is not None:
            self.anime, self.lang, self.episodes = parse_auto_search(
                "binge", self.options.search
            )
            return

        anime = self._get_anime_from_user()

        if anime is None:
            sys.exit(0)

        self.lang = lang_prompt(anime)

        episodes = pick_episode_range_prompt(anime, self.lang)

        self.anime = anime
        self.episodes = episodes

    def process(self): ...

    def show(self):
        assert self.episodes is not None
        assert self.anime is not None
        assert self.lang is not None

        for e in self.episodes:
            with DotSpinner(
                "Extracting streams for ",
                colors.BLUE,
                f"{self.anime.name} ({self.lang})",
                colors.END,
                " Episode ",
                e,
                "...",
            ) as s:
                stream = self.anime.get_video(
                    e, self.lang, preferred_quality=self.options.quality
                )
                s.ok("✔")

            self.history_list.update(self.anime, episode=e, language=self.lang)
            self.player.play_title(self.anime, stream)
            self.player.wait()

    def post(self):
        self.player.kill_player()
