import sys

from ...colors import cprint, colors
from ...misc import Entry
from ...query import query
from ...url_handler import epHandler, videourl
from ...player import get_player
from ...arg_parser import CliArgs
from ..util import binge
from .base_cli import CliBase


class BingeCli(CliBase):
    def __init__(self, options: CliArgs, rpc_client=None):
        super().__init__(options, rpc_client)
        self.entry = Entry()
        self.ep_list = []
        self.binge_list = {}
        self.player = get_player(
            self.rpc_client, self.options.optional_player
        )

    def print_header(self):
        cprint(colors.GREEN, "***Binge Mode***")

    def take_input(self):
        inp = input("Search: ")
        user_query = query(inp, self.entry)

        if user_query.get_links() == 0:
            self.exit("no search results")

        self.entry = user_query.pick_show()
        self.ep_list = epHandler(self.entry).pick_range()

    def process(self):
        ep_urls = []
        for i in self.ep_list:
            ent = Entry()
            ent.ep = int(i)
            ent.category_url = self.entry.category_url
            ep_class = epHandler(ent)
            ent = ep_class.gen_eplink()
            ep_urls.append(ent.ep_url)

        self.binge_list = {
            self.entry.show_name: {
                "ep_urls": ep_urls,
                "eps": self.ep_list,
                "category_url": self.entry.category_url,
            }
        }

    def show(self):
        binge(self.binge_list, self.options.quality, self.player)

    def post(self):
        self.player.kill_player()
