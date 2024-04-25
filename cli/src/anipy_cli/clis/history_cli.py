import sys
from typing import TYPE_CHECKING, Optional

from anipy_api.anime import Anime
from anipy_api.history import get_history
from InquirerPy import inquirer

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.colors import colors
from anipy_cli.config import Config
from anipy_cli.menus import Menu
from anipy_cli.util import DotSpinner, get_configured_player

if TYPE_CHECKING:
    from anipy_api.history import HistoryEntry
    from anipy_api.provider import ProviderStream

    from anipy_cli.arg_parser import CliArgs


class HistoryCli(CliBase):
    def __init__(self, options: "CliArgs", rpc_client=None):
        super().__init__(options, rpc_client)

        self.player = get_configured_player(
            self.rpc_client, self.options.optional_player
        )

        self.anime: Optional[Anime] = None
        self.history_entry: Optional["HistoryEntry"] = None
        self.stream: Optional["ProviderStream"] = None

    def print_header(self):
        pass

    def take_input(self):
        config = Config()
        history = list(get_history(config._history_file_path).history.values())
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
            self.history_entry,
            "...",
        ):
            self.stream = self.anime.get_video(
                self.history_entry.episode,
                self.options.quality,
                dub=self.history_entry.dub,
            )

    def show(self):
        config = Config()
        update_history(
            config._history_file_path, self.anime, self.stream.episode, self.stream.dub
        )
        self.player.play_title(self.anime, self.stream)

    def post(self):
        Menu(
            options=self.options,
            anime=self.anime,
            stream=self.stream,
            player=self.player,
            rpc_client=self.rpc_client,
        ).run()
