import sys
from typing import TYPE_CHECKING

from anipy_api.player import get_player

from anipy_cli.clis import CliBase
from anipy_cli.colors import colors
from anipy_cli.menus import Menu
from anipy_cli.util import (
    DotSpinner,
    dub_prompt,
    pick_episode_prompt,
    search_show_prompt,
    get_configured_player
)

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


# TODO: Add Resume feature
class DefaultCli(CliBase):
    def __init__(self, options: "CliArgs", rpc_client=None):
        super().__init__(options, rpc_client)

        self.player = get_configured_player(self.rpc_client, self.options.optional_player)

        self.anime = None
        self.epsiode = None
        self.stream = None
        self.dub = False

    def print_header(self):
        pass

    def take_input(self):
        anime = search_show_prompt()

        if anime is None:
            sys.exit(0)

        self.dub = dub_prompt(anime)

        episode = pick_episode_prompt(anime, self.dub)

        self.anime = anime
        self.epsiode = episode

    def process(self):
        with DotSpinner(
            "Extracting streams for ",
            colors.BLUE,
            f"{self.anime.name} ({'dub' if self.dub else 'sub'})",
            " Episode ",
            self.epsiode,
            "...",
        ):
            self.stream = self.anime.get_video(
                self.epsiode, self.options.quality, dub=self.dub
            )

    def show(self):
        self.player.play_title(self.anime, self.stream)

    def post(self):
        Menu(
            options=self.options,
            anime=self.anime,
            stream=self.stream,
            player=self.player,
            rpc_client=self.rpc_client,
        ).run()
