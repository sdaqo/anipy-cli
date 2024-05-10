import sys
from typing import TYPE_CHECKING, Optional

from anipy_api.locallist import LocalList

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.colors import colors
from anipy_cli.config import Config
from anipy_cli.menus import Menu
from anipy_cli.prompts import (
    pick_episode_prompt,
    search_show_prompt,
    lang_prompt,
    parse_auto_search,
)
from anipy_cli.util import (
    DotSpinner,
    get_configured_player,
    migrate_locallist,
)

if TYPE_CHECKING:
    from anipy_api.anime import Anime
    from anipy_api.provider import Episode, ProviderStream, LanguageTypeEnum
    from anipy_cli.arg_parser import CliArgs


# TODO: Add Resume feature
class DefaultCli(CliBase):
    def __init__(self, options: "CliArgs"):
        super().__init__(options)

        self.player = get_configured_player(self.options.optional_player)
        self.history_list = LocalList(
            Config()._history_file_path, migrate_cb=migrate_locallist
        )

        self.anime: Optional["Anime"] = None
        self.epsiode: Optional["Episode"] = None
        self.stream: Optional["ProviderStream"] = None
        self.lang: Optional["LanguageTypeEnum"] = None

    def print_header(self):
        pass

    def take_input(self):
        if self.options.search is not None:
            self.anime, self.lang, episodes = parse_auto_search(
                "default", self.options.search
            )
            self.epsiode = episodes[0]
            return

        anime = search_show_prompt("default")

        if anime is None:
            sys.exit(0)

        self.lang = lang_prompt(anime)

        episode = pick_episode_prompt(anime, self.lang)

        if episode is None:
            sys.exit(0)

        self.anime = anime
        self.epsiode = episode

    def process(self):
        assert self.anime is not None
        assert self.epsiode is not None
        assert self.lang is not None

        with DotSpinner(
            "Extracting streams for ",
            colors.BLUE,
            f"{self.anime.name} ({self.lang})",
            " Episode ",
            self.epsiode,
            "...",
        ):
            self.stream = self.anime.get_video(
                self.epsiode, self.lang, preferred_quality=self.options.quality
            )

    def show(self):
        assert self.anime is not None
        assert self.stream is not None

        self.history_list.update(
            self.anime, episode=self.epsiode, language=self.stream.language
        )
        self.player.play_title(self.anime, self.stream)

    def post(self):
        assert self.anime is not None
        assert self.stream is not None

        Menu(
            options=self.options,
            anime=self.anime,
            stream=self.stream,
            player=self.player,
        ).run()
