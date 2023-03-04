import sys
from typing import List

from anipy_cli.arg_parser import CliArgs
from anipy_cli.colors import colors, cprint
from anipy_cli.misc import Entry, error
from anipy_cli.player import PlayerBaseType
from anipy_cli.url_handler import videourl, epHandler
from anipy_cli.query import query
from anipy_cli.download import download
from anipy_cli.config import Config
from anipy_cli.cli.menus.base_menu import MenuBase, MenuOption


class Menu(MenuBase):
    def __init__(
        self, options: CliArgs, entry: Entry, player: PlayerBaseType, rpc_client=None
    ):
        self.rpc_client = rpc_client
        self.options = options
        self.entry = entry
        self.player = player

    @property
    def menu_options(self) -> List[MenuOption]:
        return [
            MenuOption("Next Episode", self.next_ep, "n"),
            MenuOption("Previous Episode", self.prev_ep, "p"),
            MenuOption("Replay Episode", self.repl_ep, "r"),
            MenuOption("Select episode", self.selec_ep, "s"),
            MenuOption("Search for Anime", self.search, "a"),
            MenuOption("Print Video Info", self.video_info, "i"),
            MenuOption("Download Episode", self.download_video, "d"),
            MenuOption("Quit", self.quit, "q"),
        ]

    def print_header(self):
        cprint(
            colors.GREEN,
            f"Playing: {self.entry.show_name} {self.entry.quality} | ",
            colors.RED,
            f"{self.entry.ep}/{self.entry.latest_ep}",
        )

    def start_ep(self):
        self.entry.embed_url = ""
        url_class = videourl(self.entry, self.options.quality)
        url_class.stream_url()
        self.entry = url_class.get_entry()
        self.player.play_title(self.entry)

    def next_ep(self):
        ep_class = epHandler(self.entry)
        self.entry = ep_class.next_ep()
        self.start_ep()
        self.print_options()

    def prev_ep(self):
        ep_class = epHandler(self.entry)
        self.entry = ep_class.prev_ep()
        self.start_ep()
        self.print_options()

    def repl_ep(self):
        self.start_ep()

    def selec_ep(self):
        ep_class = epHandler(self.entry)
        self.entry = ep_class.pick_ep()
        self.start_ep()
        self.print_options()

    def search(self):
        query_class = query(input("Search: "), self.entry)
        if query_class.get_links() == 0:
            error("no search results")
            return
        else:
            self.entry = query_class.pick_show()
            ep_class = epHandler(self.entry)
            self.entry = ep_class.pick_ep()
            self.start_ep()
            self.print_options()

    def video_info(self):
        print(f"Show Name: {self.entry.show_name}")
        print(f"Category Url: {self.entry.category_url}")
        print(f"Episode Url: {self.entry.ep_url}")
        print(f"Episode: {self.entry.ep}")
        print(f"Embed Url: {self.entry.embed_url}")
        print(f"Stream Url: {self.entry.stream_url}")
        print(f"Quality: {self.entry.quality}")

    def download_video(self):
        path = download(self.entry, self.options.quality).download()
        if Config().auto_open_dl_defaultcli:
            self.player.play_file(str(path))
        self.print_options()

    def quit(self):
        self.player.kill_player()
        sys.exit(0)
