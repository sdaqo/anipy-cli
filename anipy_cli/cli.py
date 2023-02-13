"""
Collection of 
all cli functions.
"""

import time
import os
import sys
import subprocess as sp
from copy import deepcopy
from pathlib import Path

from .mal import MAL
from .seasonal import Seasonal
from .url_handler import epHandler, videourl
from .history import history
from .misc import (
    error,
    entry,
    options,
    clear_console,
    print_names,
    seasonal_options,
    parsenum,
    mal_options,
    search_in_season_on_gogo,
)
from .player import (
    start_player,
    dc_presence_connect,
    create_mpv_controllable,
    mpv_start_stream,
)
from .query import query
from .arg_parser import parse_args
from .colors import colors, cinput, cprint
from .download import download
from .config import Config

# Make colors work in windows CMD
os.system("")

rpc_client = None
if Config().dc_presence:
    rpc_client = dc_presence_connect()


def default_cli(quality, player):
    """
    Default cli(no flags like -H or -d)
    Just prints a search prompt and then
    does the default behavior.
    """
    show_entry = entry()
    query_class = query(input("Search: "), show_entry)
    if query_class.get_links() == 0:
        sys.exit()
    show_entry = query_class.pick_show()
    ep_class = epHandler(show_entry)
    show_entry = ep_class.pick_ep()
    url_class = videourl(show_entry, quality)
    url_class.stream_url()
    show_entry = url_class.get_entry()

    mpv = None
    sub_proc = None
    if Config().reuse_mpv_window and not player and Config().player_path == "mpv":
        mpv = create_mpv_controllable()
        mpv = mpv_start_stream(show_entry, mpv, rpc_client)
    else:
        sub_proc = start_player(show_entry, rpc_client, player)

    menu(show_entry, options, sub_proc, quality, player, mpv).print_and_input()


def download_cli(quality, ffmpeg, no_season_search, path):
    """
    Cli function for the
    -d flag.
    """
    is_season_search = False

    if path is None:
        path = Config().download_folder_path

    cprint(colors.GREEN, "***Download Mode***")
    cprint(colors.GREEN, "Downloads are stored in: ", colors.END, str(path))

    show_entry = entry()
    searches = []
    show_entries = []
    if (
        not no_season_search
        and input("Search MyAnimeList for anime in Season? (y|n): \n>> ") == "y"
    ):
        searches = get_season_searches()

    else:
        another = "y"
        while another == "y":
            searches.append(input("Search: "))
            another = input("Add another search: (y|n)\n")

    for search in searches:
        links = 0
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
            sys.exit()

        if is_season_search:
            show_entry = entry()
            show_entry.show_name = search["name"]
            show_entry.category_url = search["category_url"]

        else:
            show_entry = query_class.pick_show()

        ep_class = epHandler(show_entry)
        ep_list = ep_class.pick_range()
        show_entries.append(
            {"show_entry": deepcopy(show_entry), "ep_list": deepcopy(ep_list)}
        )

    for ent in show_entries:
        show_entry = ent["show_entry"]
        ep_list = ent["ep_list"]
        for i in ep_list:
            show_entry.ep = parsenum(i)
            show_entry.embed_url = ""
            ep_class = epHandler(show_entry)
            show_entry = ep_class.gen_eplink()
            url_class = videourl(show_entry, quality)
            url_class.stream_url()
            show_entry = url_class.get_entry()
            download(show_entry, quality, ffmpeg).download()


def history_cli(quality, player):
    """
    Cli function for the -H flag, prints all of the history,
    so user is able to pick one and continue watching.
    """
    show_entry = entry()
    hist_class = history(show_entry)

    json = hist_class.read_save_data()

    if not json:
        error("no history")
        return

    shows = [x for x in json]

    for num, val in enumerate(shows, 1):
        ep = json[val]["ep"]
        col = ""
        if num % 2:
            col = colors.YELLOW
        cprint(
            colors.GREEN,
            f"[{num}]",
            colors.RED,
            f" EP: {ep}",
            colors.END,
            " | ",
            col,
            val,
        )

    while True:
        inp = cinput(colors.CYAN, "Enter Number: ")
        try:
            if int(inp) <= 0:
                error("invalid input")
        except ValueError:
            error("invalid input")

        try:
            picked = shows[int(inp) - 1]
            break

        except:
            error("invalid Input")

    show_entry.show_name = picked
    show_entry.ep = json[picked]["ep"]
    show_entry.ep_url = json[picked]["ep-link"]
    show_entry.category_url = json[picked]["category-link"]
    show_entry.latest_ep = epHandler(show_entry).get_latest()
    url_class = videourl(show_entry, quality)
    url_class.stream_url()
    show_entry = url_class.get_entry()
    sub_proc = start_player(show_entry, rpc_client, player)
    menu(show_entry, options, sub_proc, quality, player=player).print_and_input()


def binge_cli(quality, player):
    """
    Cli function for the
    -b flag.
    """
    cprint(colors.GREEN, "***Binge Mode***")

    show_entry = entry()
    query_class = query(input("Search: "), show_entry)
    query_class.get_pages()
    if query_class.get_links() == 0:
        sys.exit()
    show_entry = query_class.pick_show()
    ep_class = epHandler(show_entry)
    ep_list = ep_class.pick_range()

    ep_urls = []
    for i in ep_list:
        ent = entry()
        ent.ep = int(i)
        ent.category_url = show_entry.category_url
        ep_class = epHandler(ent)
        ent = ep_class.gen_eplink()
        ep_urls.append(ent.ep_url)

    ep_list = {
        show_entry.show_name: {
            "ep_urls": ep_urls,
            "eps": ep_list,
            "category_url": show_entry.category_url,
        }
    }

    binge(ep_list, quality, player)


def seasonal_cli(quality, no_season_search, ffmpeg, auto_update, player, path):
    s = seasonalCli(quality, no_season_search, player, ffmpeg, auto_update, path)

    if auto_update:
        s.download_latest()

    else:
        s.print_opts()
        s.take_input()


class seasonalCli:
    def __init__(
        self, quality, no_season_search, player, ffmpeg=False, auto=False, path=None
    ):
        self.entry = entry()
        self.quality = quality
        self.no_season_search = no_season_search
        self.s_class = Seasonal()
        self.ffmpeg = ffmpeg
        self.auto = auto
        self.player = player
        self.path = path
        if path is None:
            self.path = Config().seasonals_dl_path

    def print_opts(self):
        for i in seasonal_options:
            print(i)

    def take_input(self):
        while True:
            picked = cinput(colors.CYAN, "Enter option: ")
            if picked == "a":
                self.add_anime()
            elif picked == "e":
                self.del_anime()
            elif picked == "l":
                self.list_animes()
            elif picked == "d":
                self.download_latest()
            elif picked == "w":
                self.binge_latest()
            elif picked == "q":
                self.quit()
            else:
                error("invalid input")

    def add_anime(self):
        show_entry = entry()
        is_season_search = False
        searches = []
        if (
            not self.no_season_search
            and input("Search for anime in Season? (y|n): \n>> ") == "y"
        ):
            searches = get_season_searches()

        else:
            searches.append(input("Search: "))

        for search in searches:
            links = 0
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
                sys.exit()

            if is_season_search:
                show_entry = entry()
                show_entry.show_name = search["name"]
                show_entry.category_url = search["category_url"]

            else:
                show_entry = query_class.pick_show()

            picked_ep = epHandler(show_entry).pick_ep_seasonal().ep
            Seasonal().add_show(
                show_entry.show_name, show_entry.category_url, picked_ep
            )
        clear_console()
        self.print_opts()

    def del_anime(self):
        seasonals = Seasonal().list_seasonals()
        seasonals = [x[0] for x in seasonals]
        print_names(seasonals)
        while True:
            inp = cinput(colors.CYAN, "Enter Number: ")
            try:
                picked = seasonals[int(inp) - 1]
                break
            except:
                error("Invalid Input")

        Seasonal().del_show(picked)
        clear_console()
        self.print_opts()

    def list_animes(self):
        for i in Seasonal().list_seasonals():
            print(f"==> EP: {i[1]} | {i[0]}")

    def list_possible(self, latest_urls):
        for i in latest_urls:
            cprint(colors.RED, f"{i}:")
            for j in latest_urls[i]["ep_list"]:
                cprint(colors.CYAN, f"==> EP: {j[0]}")

    def download_latest(self):
        latest_urls = Seasonal().latest_eps()

        if not latest_urls:
            error("Nothing to download")
            return

        print("Stuff to be downloaded:")
        self.list_possible(latest_urls)
        if not self.auto:
            cinput(colors.RED, "Enter to continue or CTRL+C to abort.")

        for i in latest_urls:
            print(f"Downloading newest urls for {i}")
            show_entry = entry()
            show_entry.show_name = i
            for j in latest_urls[i]["ep_list"]:
                show_entry.embed_url = ""
                show_entry.ep = j[0]
                show_entry.ep_url = j[1]
                url_class = videourl(show_entry, self.quality)
                url_class.stream_url()
                show_entry = url_class.get_entry()
                download(show_entry, self.quality, self.ffmpeg, self.path).download()

        if not self.auto:
            clear_console()
            self.print_opts()

        for i in latest_urls:
            Seasonal().update_show(i, latest_urls[i]["category_url"])

    def binge_latest(self):
        latest_eps = Seasonal().latest_eps()
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

        binge(ep_dic, self.quality, self.player, mode="seasonal")

        for i in latest_eps:
            Seasonal().update_show(i, latest_eps[i]["category_url"])

        clear_console()
        self.print_opts()

    def quit(self):
        sys.exit(0)


class menu:
    """
    This is mainly a class for the cli
    interface, it should have an entry,
    with all fields filled. It also accepts
    a list of options that will be printed
    this is just a thing for flexibility.
    A sub_proc is also required this one is
    a subprocess instance returned by misc.start_player().
    """

    def __init__(self, entry, opts, sub_proc, quality, player, mpv=None) -> None:
        self.entry = entry
        self.options = opts
        self.sub_proc = sub_proc
        self.quality = quality
        self.player = player
        self.mpv = mpv

    def print_opts(self):
        for i in self.options:
            print(i)

    def print_status(self):
        clear_console()
        cprint(
            colors.GREEN,
            f"Playing: {self.entry.show_name} {self.entry.quality} | ",
            colors.RED,
            f"{self.entry.ep}/{self.entry.latest_ep}",
        )

    def print_and_input(self):
        self.print_status()
        self.print_opts()
        self.take_input()

    def kill_player(self):
        if self.mpv:
            return

        self.sub_proc.kill()

    def start_ep(self):
        self.entry.embed_url = ""
        url_class = videourl(self.entry, self.quality)
        url_class.stream_url()
        self.entry = url_class.get_entry()
        if self.mpv:
            self.mpv = mpv_start_stream(self.entry, self.mpv, rpc_client)
        else:
            self.sub_proc = start_player(self.entry, rpc_client, self.player)

    def take_input(self):
        while True:
            picked = input("Enter option: ")
            if picked == "n":
                self.next_ep()
            elif picked == "p":
                self.prev_ep()
            elif picked == "r":
                self.repl_ep()
            elif picked == "s":
                self.selec_ep()
            elif picked == "h":
                self.hist()
            elif picked == "a":
                self.search()
            elif picked == "i":
                self.video_info()
            elif picked == "d":
                self.download_video()
            elif picked == "q":
                self.quit()
            else:
                error("invalid input")

    def next_ep(self):
        self.kill_player()
        ep_class = epHandler(self.entry)
        self.entry = ep_class.next_ep()
        self.print_status()
        self.start_ep()
        self.print_opts()

    def prev_ep(self):
        self.kill_player()
        ep_class = epHandler(self.entry)
        self.entry = ep_class.prev_ep()
        self.start_ep()
        self.print_status()
        self.print_opts()

    def repl_ep(self):
        self.kill_player()
        self.start_ep()

    def selec_ep(self):
        ep_class = epHandler(self.entry)
        self.entry = ep_class.pick_ep()
        self.kill_player()
        self.start_ep()
        self.print_status()
        self.print_opts()

    def hist(self):
        self.kill_player()
        history_cli(self.quality, self.player)

    def search(self):
        query_class = query(input("Search: "), self.entry)
        if query_class.get_links() == 0:
            return
        else:
            self.entry = query_class.pick_show()
            ep_class = epHandler(self.entry)
            self.entry = ep_class.pick_ep()
            self.kill_player()
            self.start_ep()
            self.print_status()
            self.print_opts()

    def video_info(self):
        print(f"Show Name: {self.entry.show_name}")
        print(f"Category Url: {self.entry.category_url}")
        print(f"Episode Url: {self.entry.ep_url}")
        print(f"Episode: {self.entry.ep}")
        print(f"Embed Url: {self.entry.embed_url}")
        print(f"Stream Url: {self.entry.stream_url}")
        print(f"Quality: {self.entry.quality}")

    def download_video(self):
        path = download(self.entry, self.quality).download()
        if Config().auto_open_dl_defaultcli:
            player_command = [Config().player_path, str(path)]
            if os.name in ("nt", "dos"):
                sp.Popen(player_command)
            else:
                sp.Popen(player_command, stdout=sp.PIPE, stderr=sp.DEVNULL)

        self.print_status()
        self.print_opts()

    def quit(self):
        self.kill_player()
        if self.mpv:
            self.mpv.terminate()
        sys.exit(0)


def binge(ep_list, quality, player, mode=""):
    """
    Accepts ep_list like so:
        {"name" {'ep_urls': [], 'eps': [], 'category_url': }, "next_anime"...}
    """
    cprint(colors.RED, "To quit press CTRL+C")
    try:
        for i in ep_list:
            show_entry = entry()
            show_entry.show_name = i
            show_entry.category_url = ep_list[i]["category_url"]
            show_entry.latest_ep = epHandler(show_entry).get_latest()
            for url, ep in zip(ep_list[i]["ep_urls"], ep_list[i]["eps"]):

                show_entry.ep = ep
                show_entry.embed_url = ""
                show_entry.ep_url = url
                cprint(
                    colors.GREEN,
                    "Fetching links for: ",
                    colors.END,
                    show_entry.show_name,
                    colors.RED,
                    f""" | EP: {
                    show_entry.ep
                    }/{
                    show_entry.latest_ep
                    }""",
                )

                url_class = videourl(show_entry, quality)
                url_class.stream_url()
                show_entry = url_class.get_entry()
                sub_proc = start_player(show_entry, rpc_client, player)
                while True:
                    poll = sub_proc.poll()
                    if poll is not None:
                        break
                    time.sleep(0.2)
                if mode == "seasonal":
                    Seasonal().update_show(
                        show_entry.show_name, show_entry.category_url
                    )
                elif mode == "mal":
                    MAL().update_watched(show_entry.show_name, show_entry.ep)

    except KeyboardInterrupt:
        try:
            sub_proc.kill()
        except:
            pass
        sys.exit()

    return


def get_season_searches(gogo=True):
    searches = []
    selected = []
    season_year = None
    season_name = None
    while not season_year:
        try:
            season_year = int(cinput(colors.CYAN, "Season Year: "))
        except ValueError:
            print("Please enter a valid year.\n")

    while not season_name:
        season_name_input = cinput(
            colors.CYAN, "Season Name (spring|summer|fall|winter): "
        )
        if season_name_input.lower() in ["spring", "summer", "fall", "winter"]:
            season_name = season_name_input

        else:
            cprint(colors.YELLOW, "Please enter a valid season name.\n")

    if gogo:
        anime_in_season = search_in_season_on_gogo(season_name, season_year)

    else:
        anime_in_season = MAL().get_seasonal_anime(season_year, season_name)

    cprint("Anime found in {} {} Season: ".format(season_year, season_name))
    cprint(
        colors.CYAN,
        "Anime found in ",
        colors.GREEN,
        season_year,
        colors.CYAN,
        " ",
        colors.YELLOW,
        season_name,
        colors.CYAN,
        " Season: ",
    )
    anime_names = []
    for anime in anime_in_season:
        if gogo:
            anime_names.append(anime["name"])

        else:
            anime_names.append(anime["node"]["title"])

    print_names(anime_names)
    selection = cinput(colors.CYAN, "Selection: (e.g. 1, 1  3 or 1-3) \n>> ")
    if selection.__contains__("-"):
        selection_range = selection.strip(" ").split("-")
        for i in range(int(selection_range[0]) - 1, int(selection_range[1]) - 1, 1):
            selected.append(i)

    else:
        for i in selection.lstrip(" ").rstrip(" ").split(" "):
            selected.append(int(i) - 1)

    for value in selected:
        searches.append(anime_in_season[int(value)])
    return searches


def mal_cli(quality, no_season_search, ffmpeg, auto_update, player, path):
    m = MALCli(quality, player, no_season_search, ffmpeg, auto_update, path)
    if auto_update:
        m.download(mode="all")

    else:
        m.print_opts()
        m.take_input()


class MALCli:
    def __init__(
        self,
        quality,
        player,
        no_season_search=False,
        ffmpeg=False,
        auto=False,
        path=False,
    ):
        self.entry = entry()
        self.quality = quality
        self.m_class = MAL()
        self.ffmpeg = ffmpeg
        self.auto = auto
        self.player = player
        self.no_season_search = no_season_search
        self.path = path
        if path is None:
            self.path = Config().seasonals_dl_path
        if (
            not Config().mal_user
            or Config().mal_user == ""
            or not Config().mal_password
            or Config().mal_password == ""
        ):
            error(
                "MAL Credentials need to be provided in config in order to use MAL CLI. Please check your config."
            )
            sys.exit(1)

    def print_opts(self):
        for i in mal_options:
            print(i)

    def take_input(self):
        while True:
            picked = cinput(colors.END, "Enter option: ")
            if picked == "a":
                self.add_anime()
            elif picked == "e":
                self.del_anime()
            elif picked == "l":
                self.list_animes()
            elif picked == "s":
                self.sync_mal_to_seasonals()
            elif picked == "b":
                self.m_class.sync_seasonals_with_mal()
            elif picked == "d":
                self.download(mode="latest")
            elif picked == "x":
                self.download(mode="all")
            elif picked == "w":
                self.binge_latest()
            elif picked == "q":
                self.quit()
            elif picked == "m":
                self.create_gogo_maps()
            else:
                error("invalid input")
            self.print_opts()

    def add_anime(self):
        show_entry = entry()
        searches = []
        if (
            not self.no_season_search
            and input("Search for anime in Season? (y|n): \n>> ") == "y"
        ):
            searches = get_season_searches(gogo=False)

        else:
            searches.append(input("Search: "))

        #
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
                while not selected:
                    try:
                        sel_index = input("Select show (Number or c for cancel):\n")
                        if sel_index == "c":
                            skip = True
                            break
                        selected = int(sel_index)
                    except ValueError:
                        print("Please enter a valid number.")
                if skip:
                    continue
                mal_entry = temp_search[selected]

            self.m_class.update_anime_list(
                mal_entry["node"]["id"], {"status": "watching"}
            )
            self.create_gogo_maps()

        clear_console()

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
        clear_console()

    def list_animes(self):
        for i in self.m_class.get_anime_list():
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
        if not self.auto:
            cinput(colors.RED, "Enter to continue or CTRL+C to abort.")

        for i in urls:
            cprint(f"Downloading newest urls for {i}", colors.CYAN)
            show_entry = entry()
            show_entry.show_name = i
            for j in urls[i]["ep_list"]:
                show_entry.embed_url = ""
                show_entry.ep = j[0]
                show_entry.ep_url = j[1]
                url_class = videourl(show_entry, self.quality)
                url_class.stream_url()
                show_entry = url_class.get_entry()
                download(show_entry, self.quality, self.ffmpeg, self.path).download()

        if not self.auto:
            clear_console()

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

        binge(ep_dic, self.quality, player=self.player, mode="mal")

        clear_console()

    def quit(self):
        sys.exit(0)

    def sync_mal_to_seasonals(self):
        self.create_gogo_maps()

        self.m_class.sync_mal_with_seasonal()

    def manual_gogomap(self):
        self.create_gogo_maps()

    def create_gogo_maps(self):
        if not self.auto and input(
            "Try auto mapping MAL to gogo format? (y/n):\n"
        ).lower() in ["y", "yes"]:
            self.m_class.auto_map_all_without_map()
        failed_to_map = list(self.m_class.get_all_without_gogo_map())
        failed_to_map.sort(key=len, reverse=True)
        if not self.auto and len(failed_to_map) > 0:
            print("MAL Anime that failed auto-map to gogo:")
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
                    show_entry = entry()
                    query_class = query(search_name, show_entry)
                    links_query = query_class.get_links(mute=True)

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
                                links_query = query_class.get_links(mute=True)
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


def main():
    args = parse_args()

    player = None

    location = args.location
    if args.location is not None:
        location = Path(args.location)

    if args.syncplay:
        player = "syncplay"

    if args.vlc:
        player = "vlc"

    if args.delete:
        try:
            Config().history_file_path.unlink()
            cprint(colors.RED, "Done")
        except FileNotFoundError:
            error("no history file found")

    elif args.download:
        download_cli(args.quality, args.ffmpeg, args.no_season_search, location)

    elif args.binge:
        binge_cli(args.quality, player)

    elif args.seasonal:
        seasonal_cli(
            args.quality,
            args.no_season_search,
            args.ffmpeg,
            args.auto_update,
            player,
            location,
        )

    elif args.auto_update:
        seasonal_cli(
            args.quality,
            args.no_season_search,
            args.ffmpeg,
            args.auto_update,
            player,
            location,
        )

    elif args.history:
        history_cli(args.quality, player)

    elif args.config:
        print(Config()._config_file)

    elif args.mal:
        mal_cli(
            args.quality,
            args.no_season_search,
            args.ffmpeg,
            args.auto_update,
            player,
            location,
        )

    else:
        default_cli(args.quality, player)

    return
