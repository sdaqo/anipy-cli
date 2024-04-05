import sys
from typing import TYPE_CHECKING, List

from anipy_cli.cli.colors import colors, cprint
from anipy_cli.cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.cli.util import (
    DotSpinner,
    error,
    pick_episode_prompt,
    search_show_prompt,
    get_download_path,
)
from anipy_cli.config import Config
from anipy_cli.download import Downloader

if TYPE_CHECKING:
    from anipy_cli.anime import Anime
    from anipy_cli.cli.arg_parser import CliArgs
    from anipy_cli.player import PlayerBase
    from anipy_cli.provider import Episode, ProviderStream


class Menu(MenuBase):
    def __init__(
        self,
        options: "CliArgs",
        anime: "Anime",
        stream: "ProviderStream",
        player: "PlayerBase",
        rpc_client=None,
    ):
        self.rpc_client = rpc_client
        self.options = options
        self.anime = anime
        self.stream = stream
        self.player = player

    @property
    def menu_options(self) -> List["MenuOption"]:
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
            f" | {self.stream.resolution}p | ",
            colors.RED,
            f"{self.stream.episode}/{self.anime.get_episodes()[-1]}",
        )

    def _start_episode(self, episode: "Episode"):
        with DotSpinner(
            "Extracting streams for ",
            colors.BLUE,
            self.anime.name,
            " Episode ",
            episode,
            "...",
        ):
            self.stream = self.anime.get_video(episode, self.options.quality)

        self.player.play_title(self.anime, self.stream)

    def next_ep(self):
        episodes = self.anime.get_episodes()
        current_episode = episodes.index(self.stream.episode)
        if len(episodes) <= current_episode + 1:
            error("no episodes after this")
        else:
            next_episode = episodes[current_episode + 1]
            self._start_episode(next_episode)

        self.print_options()

    def prev_ep(self):
        episodes = self.anime.get_episodes()
        current_episode = episodes.index(self.stream.episode)
        if current_episode - 1 < 0:
            error("no episodes before this")
        else:
            prev_episode = episodes[current_episode - 1]
            self._start_episode(prev_episode)

        self.print_options()

    def repl_ep(self):
        self._start_episode(self.stream.episode)

    def selec_ep(self):
        episode = pick_episode_prompt(self.anime)
        if episode is None:
            return
        self._start_episode(episode)
        self.print_options()

    def search(self):
        search_result = search_show_prompt()
        if search_result is None:
            return
        self.anime = search_result
        episode = pick_episode_prompt(self.anime)
        if episode is None:
            return
        self._start_episode(episode)
        self.print_options(clear_screen=True)

    def video_info(self):
        print(f"Show Name: {self.anime.name}")
        print(f"Provider: {self.anime.provider.NAME}")
        print(f"Stream Url: {self.stream.url}")
        print(f"Quality: {self.stream.resolution}p")

    def download_video(self):
        config = Config()
        with DotSpinner("Starting Download...") as s:

            def progress_indicator(percentage: float):
                s.set_text(f"Downloading ({percentage:.1f}%)")

            def info_display(message: str):
                s.write(f"> {message}")

            downloader = Downloader(progress_indicator, info_display)

            s.set_text(
                "Extracting streams for ",
                colors.BLUE,
                self.anime.name,
                colors.END,
                " Episode ",
                self.stream.episode,
                "...",
            )

            s.set_text("Downloading...")

            path = downloader.download(
                self.stream,
                get_download_path(self.anime, self.stream),
                container=config.remux_to,
                ffmpeg=self.options.ffmpeg or config.ffmpeg_hls,
            )

        if Config().auto_open_dl_defaultcli:
            self.player.play_file(str(path))

        self.print_options()

    def quit(self):
        self.player.kill_player()
        sys.exit(0)
