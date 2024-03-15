import sys
from anipy_cli.misc import Entry
# from anipy_cli.query import query
from anipy_cli.url_handler import epHandler, videourl
from anipy_cli.player import get_player
from anipy_cli.arg_parser import CliArgs
from anipy_cli.cli.menus import Menu
from anipy_cli.cli.clis.base_cli import CliBase
from anipy_cli.cli.util import search_show_prompt, pick_episode_prompt
from anipy_cli.misc import error
from anipy_cli.anime import Anime
from typing import List
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

# Add Resume feature
class DefaultCli(CliBase):
    def __init__(self, options: CliArgs, rpc_client=None):
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
            sys.exit()

        episode =  pick_episode_prompt(anime)

        if episode is None:
            sys.exit()
        
        self.anime = anime
        self.epsiode = episode

    def process(self):
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
