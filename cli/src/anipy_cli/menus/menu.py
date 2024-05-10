import sys
from typing import TYPE_CHECKING, List

from anipy_api.download import Downloader
from anipy_api.provider import LanguageTypeEnum
from anipy_api.locallist import LocalList

from anipy_cli.colors import colors, cprint
from anipy_cli.config import Config
from anipy_cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.util import DotSpinner, error, get_download_path, migrate_locallist
from anipy_cli.prompts import pick_episode_prompt, search_show_prompt


if TYPE_CHECKING:
    from anipy_api.anime import Anime
    from anipy_api.player import PlayerBase
    from anipy_api.provider import Episode, ProviderStream

    from anipy_cli.arg_parser import CliArgs


class Menu(MenuBase):
    def __init__(
        self,
        options: "CliArgs",
        anime: "Anime",
        stream: "ProviderStream",
        player: "PlayerBase",
    ):
        self.options = options
        self.anime = anime
        self.stream = stream
        self.player = player
        self.lang = stream.language
        self.history_list = LocalList(
            Config()._history_file_path, migrate_cb=migrate_locallist
        )

    @property
    def menu_options(self) -> List["MenuOption"]:
        return [
            MenuOption("Next Episode", self.next_ep, "n"),
            MenuOption("Previous Episode", self.prev_ep, "p"),
            MenuOption("Replay Episode", self.repl_ep, "r"),
            MenuOption(
                f"Change to {'sub' if self.lang == LanguageTypeEnum.DUB else 'dub'}",
                self.change_type,
                "c",
            ),
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
            f"{self.anime.name} ({self.lang})",
            colors.GREEN,
            f" | {self.stream.resolution}p | ",
            colors.RED,
            f"{self.stream.episode}/{self.anime.get_episodes(self.lang)[-1]}",
        )

    def _start_episode(self, episode: "Episode"):
        with DotSpinner(
            "Extracting streams for ",
            colors.BLUE,
            f"{self.anime.name} ({self.lang})",
            " Episode ",
            episode,
            "...",
        ):
            self.stream = self.anime.get_video(
                episode, self.lang, preferred_quality=self.options.quality
            )

        self.history_list.update(self.anime, episode=episode, language=self.lang)
        self.player.play_title(self.anime, self.stream)

    def next_ep(self):
        episodes = self.anime.get_episodes(self.lang)
        current_episode = episodes.index(self.stream.episode)
        if len(episodes) <= current_episode + 1:
            error("no episodes after this")
        else:
            next_episode = episodes[current_episode + 1]
            self._start_episode(next_episode)

        self.print_options()

    def prev_ep(self):
        episodes = self.anime.get_episodes(self.lang)
        current_episode = episodes.index(self.stream.episode)
        if current_episode - 1 < 0:
            error("no episodes before this")
        else:
            prev_episode = episodes[current_episode - 1]
            self._start_episode(prev_episode)

        self.print_options()

    def repl_ep(self):
        self._start_episode(self.stream.episode)

    def change_type(self):
        to_change = (
            LanguageTypeEnum.DUB
            if self.lang == LanguageTypeEnum.SUB
            else LanguageTypeEnum.SUB
        )

        if to_change not in self.anime.languages:
            error(f"this anime does not have a {to_change} version")
            return

        if self.stream.episode not in self.anime.get_episodes(to_change):
            error(
                f"the current episode ({self.stream.episode}) is not available in {to_change}, not switching..."
            )
            return

        self.lang = to_change
        self.repl_ep()
        self.print_options()

    def selec_ep(self):
        episode = pick_episode_prompt(self.anime, self.lang)
        if episode is None:
            return
        self._start_episode(episode)
        self.print_options()

    def search(self):
        search_result = search_show_prompt("default")
        if search_result is None:
            return
        self.anime = search_result
        episode = pick_episode_prompt(self.anime, self.lang)
        if episode is None:
            return
        self._start_episode(episode)
        self.print_options()

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
                f"{self.anime.name} ({self.lang})",
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
