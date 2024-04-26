import sys
from typing import TYPE_CHECKING

from anipy_api.history import update_history

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.colors import colors, cprint
from anipy_cli.config import Config
from anipy_cli.util import (
    DotSpinner,
    lang_prompt,
    get_configured_player,
    parse_auto_search,
    pick_episode_range_prompt,
    search_show_prompt,
)

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


class BingeCli(CliBase):
    def __init__(self, options: "CliArgs", rpc_client=None):
        super().__init__(options, rpc_client)

        self.player = get_configured_player(
            self.rpc_client, self.options.optional_player
        )

        self.anime = None
        self.episodes = None
        self.lang = None

    def print_header(self):
        cprint(colors.GREEN, "***Binge Mode***")

    def take_input(self):
        if self.options.search is not None:
            self.anime, self.lang, self.episodes = parse_auto_search("binge", self.options.search)
            return

        anime = search_show_prompt("binge")

        if anime is None:
            sys.exit(0)

        self.lang = lang_prompt(anime)

        episodes = pick_episode_range_prompt(anime, self.lang)

        self.anime = anime
        self.episodes = episodes

    def process(self): ...

    def show(self):
        config = Config()
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
                stream = self.anime.get_video(e, self.lang, preferred_quality=self.options.quality)
                s.ok("✔")

            update_history(config._history_file_path, self.anime, e, self.lang)
            self.player.play_title(self.anime, stream)
            self.player.wait()

    def post(self):
        self.player.kill_player()