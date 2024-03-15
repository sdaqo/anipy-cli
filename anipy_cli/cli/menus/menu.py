import sys
import os
from typing import List

from anipy_cli.arg_parser import CliArgs
from anipy_cli.colors import colors, cprint
from anipy_cli.misc import Entry, error, clear_console
from anipy_cli.player import PlayerBaseType
from anipy_cli.provider import ProviderStream
from anipy_cli.url_handler import videourl, epHandler
from anipy_cli.query import query
from anipy_cli.download import download
from anipy_cli.config import Config
from anipy_cli.cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.anime import Anime


class Menu(MenuBase):
    def __init__(
        self, options: CliArgs, anime: Anime, stream: ProviderStream, player: PlayerBaseType, rpc_client=None
    ):
        self.rpc_client = rpc_client
        self.options = options
        self.anime = anime
        self.stream = stream
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
            "Playing: ",
            colors.BLUE,
            self.anime.name,
            colors.GREEN,
            f" | {self.stream.resolution} | ",
            colors.RED,
            f"{self.stream.episode}/{self.anime.get_episodes()[-1]}",
        )


    def next_ep(self):
        episodes = self.anime.get_episodes()
        current_episode = episodes.index(self.stream.episode)
        if len(episodes) <= current_episode + 1:
            error("no episodes after this")
        else:
            next_episode = episodes[current_episode + 1]
            self.stream = self.anime.get_video(next_episode, self.options.quality)
            self.player.play_title(self.anime, self.stream)

        self.print_options()

    def prev_ep(self):
        episodes = self.anime.get_episodes()
        current_episode = episodes.index(self.stream.episode)
        if current_episode - 1 < 0:
            error("no episodes before this")
        else:
            next_episode = episodes[current_episode - 1]
            self.stream = self.anime.get_video(next_episode, self.options.quality)
            self.player.play_title(self.anime, self.stream)

        self.print_options()

    def repl_ep(self):
        self.stream = self.anime.get_video(self.stream.episode, self.options.quality)
        self.player.play_title(self.anime, self.stream)

    def selec_ep(self):
        ep_class = epHandler(self.entry)
        self.entry = ep_class.pick_ep()
        self.start_ep()
        self.print_options()

    def search(self):
        clear_console()
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
        print(f"Show Name: {self.anime.name}")
        print(f"Provider: {self.anime.provider.name()}")
        print(f"Stream Url: {self.stream.url}")
        print(f"Quality: {self.stream.resolution}P")

    def download_video(self):
        path = download(self.entry, self.options.quality).download()
        if Config().auto_open_dl_defaultcli:
            self.player.play_file(str(path))
        self.print_options()

    def quit(self):
        self.player.kill_player()
        sys.exit(0)
