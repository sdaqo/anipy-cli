import sys

from anipy_cli.misc import Entry
from anipy_cli.query import query
from anipy_cli.url_handler import epHandler, videourl
from anipy_cli.player import get_player
from anipy_cli.arg_parser import CliArgs
from anipy_cli.cli.menus import Menu
from anipy_cli.cli.clis.base_cli import CliBase


class DefaultCli(CliBase):
    def __init__(self, options: CliArgs, rpc_client=None):
        super().__init__(options, rpc_client)

        self.entry = Entry()
        self.player = get_player(self.rpc_client, self.options.optional_player)

    def print_header(self):
        pass

    def take_input(self):
        inp = input("Search: ")
        user_query = query(inp, self.entry)

        if user_query.get_links() == 0:
            self.exit("no search results")

        self.entry = user_query.pick_show()
        self.entry = epHandler(self.entry).pick_ep()

    def process(self):
        url_parser = videourl(self.entry, self.options.quality)
        url_parser.stream_url()
        self.entry = url_parser.get_entry()

    def show(self):
        self.player.play_title(self.entry)

    def post(self):
        Menu(
            options=self.options,
            entry=self.entry,
            player=self.player,
            rpc_client=self.rpc_client,
        ).run()
