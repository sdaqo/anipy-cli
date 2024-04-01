import sys
from typing import List, Optional
from anipy_cli.colors import cprint, colors
from anipy_cli.player import get_player
from anipy_cli.arg_parser import CliArgs
from anipy_cli.cli.util import search_show_prompt, pick_episode_range_prompt, DotSpinner
from anipy_cli.cli.clis.base_cli import CliBase
from anipy_cli.anime import Anime
from anipy_cli.provider import Episode


class BingeCli(CliBase):
    def __init__(self, options: CliArgs, rpc_client=None):
        super().__init__(options, rpc_client)

        self.player = get_player(self.rpc_client, self.options.optional_player)

        self.anime: Optional[Anime] = None
        self.episodes: Optional[List[Episode]] = None

    def print_header(self):
        cprint(colors.GREEN, "***Binge Mode***")

    def take_input(self):
        anime = search_show_prompt()

        if anime is None:
            sys.exit()

        episodes = pick_episode_range_prompt(anime)

        self.anime = anime
        self.episodes = episodes

    def process(self): ...

    def show(self):
        for e in self.episodes:
            with DotSpinner(
                "Extracting streams for ",
                colors.BLUE,
                self.anime.name,
                colors.END,
                " Episode ",
                e,
                "...",
            ) as s:
                stream = self.anime.get_video(e, self.options.quality)
                s.ok("✔")

            self.player.play_title(self.anime, stream)
            self.player.wait()

    def post(self):
        self.player.kill_player()
