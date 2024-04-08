import sys
from typing import TYPE_CHECKING, List, Optional
from anipy_cli.cli.colors import cprint, colors
from anipy_cli.player import get_player
from anipy_cli.cli.util import (
    DotSpinner,
    error,
    search_show_prompt,
    pick_episode_range_prompt,
    dub_prompt,
    DotSpinner
)
from anipy_cli.cli.clis.base_cli import CliBase

if TYPE_CHECKING:
    from anipy_cli.anime import Anime
    from anipy_cli.provider import Episode
    from anipy_cli.cli.arg_parser import CliArgs


class BingeCli(CliBase):
    def __init__(self, options: "CliArgs", rpc_client=None):
        super().__init__(options, rpc_client)

        self.player = get_player(self.rpc_client, self.options.optional_player)

        self.anime: Optional["Anime"] = None
        self.episodes: Optional[List["Episode"]] = None
        self.dub = False

    def print_header(self):
        cprint(colors.GREEN, "***Binge Mode***")

    def take_input(self):
        anime = search_show_prompt()

        if anime is None:
            sys.exit(0)

        self.dub = dub_prompt(anime)

        episodes = pick_episode_range_prompt(anime, self.dub)

        self.anime = anime
        self.episodes = episodes

    def process(self): ...

    def show(self):
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

            self.player.play_title(self.anime, stream)
            self.player.wait()

    def post(self):
        self.player.kill_player()
