from typing import List

from anipy_cli.arg_parser import CliArgs
from anipy_cli.colors import colors, cprint, cinput
from anipy_cli.misc import Entry, print_names, error
from anipy_cli.player import get_player
from anipy_cli.url_handler import videourl
from anipy_cli.query import query
from anipy_cli.download import download
from anipy_cli.config import Config
from anipy_cli.mal import MAL
from anipy_cli.cli.util import binge, get_season_searches
from anipy_cli.cli.menus.base_menu import MenuBase, MenuOption


class MALMenu(MenuBase):
    def __init__(self, options: CliArgs, rpc_client=None):
        self.entry = Entry()
        self.options = options
        self.rpc_client = rpc_client

        self.dl_path = Config().seasonals_dl_path
        if options.location:
            self.dl_path = options.location

        user = None
        if Config().mal_user and Config().mal_user != "":
            user = Config().mal_user

        if options.mal_password is not None and options.mal_password != "":
            password = options.mal_password
        else:
            password = Config().mal_password
        if not password or password == "":
            password = None

        if user is None or password is None:
            cprint(colors.ERROR, "Missing credentials!\n")
            cprint(
                colors.CYAN,
                "In order to use the MAL-Mode, you need to specify your username and password.\n",
            )
            cprint(
                colors.CYAN, "Those can be specified in the anipy-cli config file.\n"
            )

        if user is None:
            while not user:
                user_input = cinput(
                    colors.CYAN,
                    "Please enter your MyAnimeList ",
                    colors.YELLOW,
                    "Username ",
                    colors.CYAN,
                    ":\n",
                )
                if user_input and user_input != "":
                    user = user_input

        if password is None:
            cprint(
                colors.MAGENTA,
                "The password can also be passed with the '--mal-password' parameter.",
            )
            while not password:
                pw_input = cinput(
                    colors.CYAN,
                    "Please enter your MyAnimeList ",
                    colors.YELLOW,
                    "Password ",
                    colors.CYAN,
                    ":\n",
                )
                if pw_input and pw_input != "":
                    password = pw_input

        self.m_class = MAL(user, password)

    def print_header(self):
        pass

    @property
    def menu_options(self) -> List[MenuOption]:
        return [
            MenuOption("Add Anime", self.add_anime, "a"),
            MenuOption("Delete one anime from mal list", self.del_anime, "e"),
            MenuOption("List anime in mal list", self.list_animes, "l"),
            MenuOption("Map MAL anime to gogo Links", self.create_gogo_maps, "m"),
            MenuOption("Sync MAL list into seasonals", self.sync_mal_to_seasonals, "s"),
            MenuOption(
                "Sync seasonals into MAL list",
                self.m_class.sync_seasonals_with_mal,
                "b",
            ),
            MenuOption(
                "Download newest episodes", lambda: self.download(mode="latest"), "d"
            ),
            MenuOption("Download all episodes", lambda: self.download(mode="all"), "x"),
            MenuOption("Binge watch newest episodes", self.binge_latest, "w"),
            MenuOption("Quit", self.quit, "q"),
        ]

    def add_anime(self):
        searches = []
        if (
            not self.options.no_season_search
            and input("Search for anime in Season? (y|n): \n>> ") == "y"
        ):
            searches = get_season_searches(gogo=False)

        else:
            searches.append(input("Search: "))

        for search in searches:
            if isinstance(search, dict):
                mal_entry = search

            else:
                print("\nCurrent: ", search)
                temp_search = self.m_class.get_anime(search)
                names = [item["node"]["title"] for item in temp_search]
                print_names(names)
                selected = False
                skip = False
                while selected is False:
                    try:
                        sel_index = input("Select show (Number or c for cancel):\n")
                        if sel_index == "c":
                            skip = True
                            break
                        selected = int(sel_index) - 1
                    except ValueError:
                        print("Please enter a valid number.")
                if skip:
                    continue
                mal_entry = temp_search[selected]

            self.m_class.update_anime_list(
                mal_entry["node"]["id"], {"status": "watching"}
            )
            self.create_gogo_maps()

        self.print_options()

    def del_anime(self):
        mal_list = self.m_class.get_anime_list()
        mal_list = [x for x in mal_list]
        mal_names = [n["node"]["title"] for n in mal_list]
        print_names(mal_names)
        while True:
            inp = cinput(colors.CYAN, "Enter Number: ")
            try:
                picked = mal_list[int(inp) - 1]["node"]["id"]
                break
            except:
                error("Invalid Input")

        self.m_class.del_show(picked)
        self.print_options()

    def list_animes(self):
        mal_list = self.m_class.get_anime_list()
        for i in mal_list:
            status = i["node"]["my_list_status"]["status"]

            if status == "completed":
                color = colors.MAGENTA
            elif status == "on_hold":
                color = colors.YELLOW
            elif status == "plan_to_watch":
                color = colors.BLUE
            elif status == "dropped":
                color = colors.ERROR
            else:
                color = colors.GREEN

            cprint(
                colors.CYAN,
                "==> Last watched EP: {}".format(
                    i["node"]["my_list_status"]["num_episodes_watched"]
                ),
                color,
                " | ({}) | ".format(status),
                colors.CYAN,
                i["node"]["title"],
            )
        # List is empty
        if not mal_list:
            cprint(colors.YELLOW, "No anime found.\nAdd an anime to your list first.")

        input("Enter to continue")
        self.print_options()

    def list_possible(self, latest_urls):
        for i in latest_urls:
            cprint(colors.RED, f"{i}:")
            for j in latest_urls[i]["ep_list"]:
                cprint(colors.CYAN, f"==> EP: {j[0]}")

    def download(self, mode="all"):
        print("Preparing list of episodes...")
        if mode == "latest":
            urls = self.m_class.latest_eps()

        else:
            urls = self.m_class.latest_eps(all_eps=True)

        if not urls:
            error("Nothing to download")
            return

        cprint(colors.CYAN, "Stuff to be downloaded:")
        self.list_possible(urls)
        if not self.options.auto_update:
            cinput(colors.RED, "Enter to continue or CTRL+C to abort.")

        for i in urls:
            cprint(f"Downloading newest urls for {i}", colors.CYAN)
            show_entry = Entry()
            show_entry.show_name = i
            for j in urls[i]["ep_list"]:
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

    def binge_latest(self):
        latest_eps = self.m_class.latest_eps()
        cprint(colors.CYAN, "Stuff to be watched:")
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
        binge(
            ep_dic,
            self.options.quality,
            player=player,
            mode="mal",
            mal_class=self.m_class,
        )
        player.kill_player()
        self.print_options()

    def sync_mal_to_seasonals(self):
        self.create_gogo_maps()

        self.m_class.sync_mal_with_seasonal()

    def manual_gogomap(self):
        self.create_gogo_maps()

    def create_gogo_maps(self):
        if not self.options.auto_update and input(
            "Try auto mapping MAL to gogo format? (y/n):\n"
        ).lower() in ["y", "yes"]:
            self.m_class.auto_map_all_without_map()
        failed_to_map = list(self.m_class.get_all_without_gogo_map())
        failed_to_map.sort(key=len, reverse=True)
        if not self.options.auto_update and len(failed_to_map) > 0:
            cprint(colors.YELLOW, "Some Anime failed auto-mapping...")
            cprint(colors.GREEN, "Select Anime for manual mapping:\n")
            selected = []
            searches = []

            print_names(failed_to_map)
            print("Selection: (e.g. 1, 1  3, 1-3 or * [for all]) \n")
            cprint(colors.YELLOW, "Enter or n to skip...")
            selection = cinput(colors.GREEN, ">>")
            if selection.__contains__("-"):
                selection_range = selection.strip(" ").split("-")
                for i in range(
                    int(selection_range[0]) - 1, int(selection_range[1]) - 1, 1
                ):
                    selected.append(i)

            elif selection in ["all", "*"]:
                selected = range(0, len(failed_to_map) - 1)
            elif selection in ["", "n", "N"]:
                selected = []

            else:
                for i in selection.strip(" ").split(" "):
                    selected.append(int(i) - 1)

            for value in selected:
                show_entries = []
                done = False
                search_name = failed_to_map[value]
                while not done:
                    cprint(
                        colors.GREEN,
                        "Current: ",
                        colors.CYAN,
                        f"{failed_to_map[value]}\n",
                    )
                    show_entry = Entry()
                    query_class = query(search_name, show_entry)
                    links_query = query_class.get_links()

                    if not links_query:
                        skip = False
                        while not links_query and not skip:
                            cprint(
                                colors.ERROR,
                                "No search results for ",
                                colors.YELLOW,
                                failed_to_map[value],
                            )
                            cprint(
                                colors.GREEN,
                                "Sometimes the names on GoGo are too different from the ones on MAL.\n",
                            )
                            cprint(colors.CYAN, "Try custom name for mapping? (Y/N):\n")
                            if input().lower() == "y":
                                query_class = query(
                                    cinput(
                                        colors.GREEN,
                                        "Enter Search String to search on GoGo:\n",
                                    ),
                                    show_entry,
                                )
                                links_query = query_class.get_links()
                                if links_query:
                                    show = query_class.pick_show(cancelable=True)
                                    if show:
                                        show_entries.append(show_entry)
                                        mapped = self.m_class.manual_map_gogo_mal(
                                            failed_to_map[value],
                                            {
                                                "link": show_entry.category_url,
                                                "name": show_entry.show_name,
                                            },
                                        )
                                        if mapped:
                                            del failed_to_map[value]
                                            del selected[value]
                            else:
                                print("Skipping show")
                                skip = True
                                done = True
                    elif links_query[0] != 0:
                        links, names = links_query
                        search_another = True
                        while search_another and len(links) > 0:
                            show = query_class.pick_show(cancelable=True)
                            if show:
                                show_entries.append(show_entry)
                                self.m_class.manual_map_gogo_mal(
                                    failed_to_map[value],
                                    {
                                        "link": show_entry.category_url,
                                        "name": show_entry.show_name,
                                    },
                                )

                                links.remove(
                                    "/category/"
                                    + show_entry.category_url.split("/category/")[1]
                                )
                                names.remove(show_entry.show_name)
                                print(
                                    f"{colors.GREEN} Added {show_entry.show_name} ...{colors.END}"
                                )
                                if input(
                                    f"Add another show map to {failed_to_map[value]}? (y/n):\n"
                                ).lower() not in ["y", "yes"]:
                                    search_another = False
                        done = True
                    else:
                        search_name_parts = search_name.split(" ")
                        if len(search_name_parts) <= 1:
                            print(
                                f"{colors.YELLOW}Could not find {failed_to_map[value]} on gogo.{colors.END}"
                            )
                            done = True
                        else:
                            print(
                                f"{colors.YELLOW} Nothing found. Trying to shorten name...{colors.END}"
                            )

                            search_name_parts.pop()
                            search_name = " ".join(search_name_parts)
        self.m_class.write_save_data()
        self.m_class.write_mal_list()
