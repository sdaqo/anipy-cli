import sys
from typing import TYPE_CHECKING, Optional

from anipy_api.history import update_history

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.colors import colors
from anipy_cli.config import Config
from anipy_cli.menus import Menu
from anipy_cli.util import (
    DotSpinner,
    get_configured_player,
    lang_prompt,
    parse_auto_search,
    pick_episode_prompt,
    search_show_prompt,
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

        self.anime = anime
        self.epsiode = episode

    def process(self):
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
        config = Config()
        update_history(config._history_file_path, self.anime, self.epsiode, self.lang)
        self.player.play_title(self.anime, self.stream)

    def post(self):
        Menu(
            options=self.options,
            anime=self.anime,
            stream=self.stream,
            player=self.player,
        ).run()
