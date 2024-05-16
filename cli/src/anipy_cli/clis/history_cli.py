import sys
from typing import TYPE_CHECKING, Optional

from anipy_api.anime import Anime
from anipy_api.locallist import LocalList, LocalListEntry
from InquirerPy import inquirer

from anipy_cli.clis.base_cli import CliBase
from anipy_cli.colors import colors
from anipy_cli.config import Config
from anipy_cli.menus import Menu
from anipy_cli.util import DotSpinner, get_configured_player, migrate_locallist

if TYPE_CHECKING:
    from anipy_api.provider import ProviderStream

    from anipy_cli.arg_parser import CliArgs


class HistoryCli(CliBase):
    def __init__(self, options: "CliArgs"):
        super().__init__(options)

        self.player = get_configured_player(self.options.optional_player)
        self.history_list = LocalList(
            Config()._history_file_path, migrate_cb=migrate_locallist
        )

        self.anime: Optional[Anime] = None
        self.history_entry: Optional["LocalListEntry"] = None
        self.stream: Optional["ProviderStream"] = None

    def print_header(self):
        pass

    def take_input(self):
        history = self.history_list.get_all()
        history.sort(key=lambda h: h.timestamp, reverse=True)

        if not history:
            print("You have no History, exiting")
            sys.exit(0)

        entry = inquirer.fuzzy(  # type: ignore
            message="Select History Entry:",
            choices=history,
            long_instruction="To cancel this prompt press ctrl+z",
            mandatory=False,
        ).execute()

        if entry is None:
            sys.exit(0)

        self.history_entry = entry
        self.anime = Anime.from_local_list_entry(entry)

    def process(self):
        assert self.anime is not None
        assert self.history_entry is not None

        with DotSpinner(
            "Extracting streams for ",
            colors.BLUE,
            self.history_entry,
            "...",
        ):
            self.stream = self.anime.get_video(
                self.history_entry.episode,
                self.history_entry.language,
                preferred_quality=self.options.quality,
            )

    def show(self):
        assert self.anime is not None
        assert self.stream is not None

        self.player.play_title(self.anime, self.stream)
        self.history_list.update(
            self.anime,
            episode=self.stream.episode,
            language=self.stream.language,
        )

    def post(self):
        assert self.anime is not None
        assert self.stream is not None

        Menu(
            options=self.options,
            anime=self.anime,
            stream=self.stream,
            player=self.player,
        ).run()
