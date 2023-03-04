import sys
from typing import List

from anipy_cli.arg_parser import CliArgs
from anipy_cli.colors import colors, cprint, cinput
from anipy_cli.misc import Entry, print_names, error
from anipy_cli.player import get_player
from anipy_cli.url_handler import videourl, epHandler
from anipy_cli.query import query
from anipy_cli.download import download
from anipy_cli.config import Config
from anipy_cli.seasonal import Seasonal
from anipy_cli.cli.util import get_season_searches, binge
from anipy_cli.cli.menus.base_menu import MenuBase, MenuOption


class SeasonalMenu(MenuBase, Seasonal):
    def __init__(self, options: CliArgs, rpc_client=None):
        super().__init__()

        self.rpc_client = rpc_client
        self.options = options
        self.entry = Entry()
        self.dl_path = Config().seasonals_dl_path
        if options.location:
            self.dl_path = options.location

    @property
    def menu_options(self) -> List[MenuOption]:
        return [
            MenuOption("Add Anime", self.add_anime, "a"),
            MenuOption("Delete one anime from seasonals", self.del_anime, "e"),
            MenuOption("List anime in seasonals file", self.list_animes, "l"),
            MenuOption("Download newest episodes", self.download_latest, "d"),
            MenuOption("Binge watch newest episodes", self.binge_latest, "w"),
            MenuOption("Quit", self.quit, "q"),
        ]

    def print_header(self):
        pass

    def add_anime(self):
        show_entry = Entry()
        is_season_search = False
        searches = []
        if (
            not self.options.no_season_search
            and input("Search for anime in Season? (y|n): \n>> ") == "y"
        ):
            searches = get_season_searches()

        else:
            searches.append(input("Search: "))

        for search in searches:
            query_class = None
            if isinstance(search, dict):
                is_season_search = True
                links = [search["category_url"]]

            else:
                print("\nCurrent: ", search)
                query_class = query(search, show_entry)
                query_class.get_pages()
                links = query_class.get_links()

            if links == 0:
                error("no search results")
                input("Enter to continue")
                self.print_options()

            if is_season_search:
                show_entry = Entry()
                show_entry.show_name = search["name"]
                show_entry.category_url = search["category_url"]

            else:
                show_entry = query_class.pick_show()

            picked_ep = epHandler(show_entry).pick_ep_seasonal().ep
            self.add_show(show_entry.show_name, show_entry.category_url, picked_ep)
        self.print_options()

    def del_anime(self):
        seasonals = self.list_seasonals()
        seasonals = [x[0] for x in seasonals]
        print_names(seasonals)
        while True:
            inp = cinput(colors.CYAN, "Enter Number: ")
            try:
                picked = seasonals[int(inp) - 1]
                break
            except:
                error("Invalid Input")

        self.del_show(picked)

        self.print_options()

    def list_animes(self):
        for i in self.list_seasonals():
            print(f"==> EP: {i[1]} | {i[0]}")

    def list_possible(self, latest_urls):
        for i in latest_urls:
            cprint(colors.RED, f"{i}:")
            for j in latest_urls[i]["ep_list"]:
                cprint(colors.CYAN, f"==> EP: {j[0]}")

    def download_latest(self):
        latest_urls = self.latest_eps()

        if not latest_urls:
            error("Nothing to download")
            return

        print("Stuff to be downloaded:")
        self.list_possible(latest_urls)
        if not self.options.auto_update:
            cinput(colors.RED, "Enter to continue or CTRL+C to abort.")

        for i in latest_urls:
            print(f"Downloading newest urls for {i}")
            show_entry = Entry()
            show_entry.show_name = i
            for j in latest_urls[i]["ep_list"]:
                show_entry.embed_url = ""
                show_entry.ep = j[0]
                show_entry.ep_url = j[1]
                url_class = videourl(show_entry, self.options.quality)
                url_class.stream_url()
                show_entry = url_class.get_entry()
                download(
                    show_entry, self.options.quality, self.options.ffmpeg, self.dl_path
                ).download()

        if not self.options.auto_update:
            self.print_options()

        for i in latest_urls:
            self.update_show(i, latest_urls[i]["category_url"])

    def binge_latest(self):
        latest_eps = self.latest_eps()
        print("Stuff to be watched:")
        self.list_possible(latest_eps)
        cinput(colors.RED, "Enter to continue or CTRL+C to abort.")
        ep_list = []
        ep_urls = []
        ep_dic = {}
        for i in latest_eps:
            for j in latest_eps[i]["ep_list"]:
                ep_list.append(j[0])
                ep_urls.append(j[1])

            ep_dic.update(
                {
                    i: {
                        "ep_urls": [x for x in ep_urls],
                        "eps": [x for x in ep_list],
                        "category_url": latest_eps[i]["category_url"],
                    }
                }
            )
            ep_list.clear()
            ep_urls.clear()

        player = get_player(self.rpc_client, self.options.optional_player)
        binge(ep_dic, self.options.quality, player, mode="seasonal")
        player.kill_player()
        for i in latest_eps:
            self.update_show(i, latest_eps[i]["category_url"])

        self.print_options()
