import sys
from InquirerPy import inquirer
from typing import TYPE_CHECKING, Optional

from anipy_cli.cli.menus import Menu
from anipy_cli.cli.clis.base_cli import CliBase
from anipy_cli.anime import Anime
from anipy_cli.cli.util import DotSpinner
from anipy_cli.cli.colors import colors
from anipy_cli.history import get_history
from anipy_cli.player import get_player

if TYPE_CHECKING:
    from anipy_cli.cli.arg_parser import CliArgs
    from anipy_cli.history import HistoryEntry
    from anipy_cli.provider import ProviderStream


class HistoryCli(CliBase):
    def __init__(self, options: "CliArgs", rpc_client=None):
        super().__init__(options, rpc_client)

        self.player = get_player(self.rpc_client, self.options.optional_player)

        self.anime: Optional[Anime] = None
        self.history_entry: Optional["HistoryEntry"] = None
        self.stream: Optional["ProviderStream"] = None

    def print_header(self):
        pass

    def take_input(self):
        history = list(get_history().history.values())
        history.sort(key=lambda h: h.timestamp, reverse=True)

        if not history:
            print("You have no History, exiting")
            sys.exit(0)

        entry = inquirer.select(
            message="Select History Entry:",
            choices=history,
            long_instruction="Press Ctrl",
        ).execute()

        self.history_entry = entry
        self.anime = Anime.from_history_entry(entry)

    def process(self):
        with DotSpinner(
            "Extracting streams for ",
            colors.BLUE,
            self.anime.name,
            " Episode ",
            self.history_entry.episode,
            "...",
        ):
            self.stream = self.anime.get_video(
                self.history_entry.episode, self.options.quality
            )

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
