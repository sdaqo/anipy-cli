from typing import TYPE_CHECKING, no_type_check

from anipy_cli.player import get_player
from anipy_cli.cli.menus import Menu
from anipy_cli.cli.clis.base_cli import CliBase
from anipy_cli.cli.util import search_show_prompt, pick_episode_prompt, DotSpinner
from anipy_cli.cli.colors import colors

if TYPE_CHECKING:
    from anipy_cli.cli.arg_parser import CliArgs


# TODO: Add Resume feature
class DefaultCli(CliBase):
    def __init__(self, options: 'CliArgs', rpc_client=None):
        super().__init__(options, rpc_client)

        self.player = get_player(self.rpc_client, self.options.optional_player)

        self.anime = None
        self.epsiode = None
        self.stream = None

    def print_header(self):
        pass

    def take_input(self):
        anime = search_show_prompt()

        if anime is None:
            self.exit("No Anime Chosen")

        episode = pick_episode_prompt(anime)

        self.anime = anime
        self.epsiode = episode

    def process(self):
        with DotSpinner(
            "Extracting streams for ",
            colors.BLUE,
            self.anime.name,
            " Episode ",
            self.epsiode,
            "...",
        ):
            self.stream = self.anime.get_video(self.epsiode, self.options.quality) 

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
