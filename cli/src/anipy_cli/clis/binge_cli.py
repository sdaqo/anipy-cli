import sys
from typing import TYPE_CHECKING, List, Optional

from anipy_api.history import update_history

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.colors import colors, cprint
from anipy_cli.config import Config
from anipy_cli.util import (
    DotSpinner,
    dub_prompt,
    get_configured_player,
    parse_auto_search,
    pick_episode_range_prompt,
    search_show_prompt,
)

if TYPE_CHECKING:
    from anipy_api.anime import Anime
    from anipy_api.provider import Episode

    from anipy_cli.arg_parser import CliArgs


class BingeCli(CliBase):
    def __init__(self, options: "CliArgs", rpc_client=None):
        super().__init__(options, rpc_client)

        self.player = get_configured_player(
            self.rpc_client, self.options.optional_player
        )

        self.anime: Optional["Anime"] = None
        self.episodes: Optional[List["Episode"]] = None
        self.dub = False

    def print_header(self):
        cprint(colors.GREEN, "***Binge Mode***")

    def take_input(self):
        if self.options.search is not None:
            self.anime, self.dub, self.episodes = parse_auto_search(self.options.search)
            return

        anime = search_show_prompt()

        if anime is None:
            sys.exit(0)

        self.dub = dub_prompt(anime)

        episodes = pick_episode_range_prompt(anime, self.dub)

        self.anime = anime
        self.episodes = episodes

    def process(self): ...

    def show(self):
        config = Config()
        for e in self.episodes:
            with DotSpinner(
                "Extracting streams for ",
                colors.BLUE,
                f"{self.anime.name} ({'dub' if self.dub else 'sub'})",
                colors.END,
                " Episode ",
                e,
                "...",
            ) as s:
                stream = self.anime.get_video(e, self.options.quality, dub=self.dub)
                s.ok("✔")

            update_history(config._history_file_path, self.anime, e, self.dub)
            self.player.play_title(self.anime, stream)
            self.player.wait()

    def post(self):
        self.player.kill_player()
