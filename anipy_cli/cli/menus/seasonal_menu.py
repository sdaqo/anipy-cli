import sys
from typing import TYPE_CHECKING, List, Tuple

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.utils import get_style

from anipy_cli.anime import Anime
from anipy_cli.cli.colors import colors
from anipy_cli.cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.cli.util import (
    DotSpinner,
    dub_prompt,
    error,
    get_download_path,
    pick_episode_prompt,
    search_show_prompt,
)
from anipy_cli.config import Config
from anipy_cli.download import Downloader
from anipy_cli.player import get_player
from anipy_cli.provider.base import Episode
from anipy_cli.seasonal import (
    SeasonalEntry,
    delete_seasonal,
    get_seasonals,
    update_seasonal,
)

if TYPE_CHECKING:
    from anipy_cli.cli.arg_parser import CliArgs


class SeasonalMenu(MenuBase):
    def __init__(self, options: "CliArgs", rpc_client=None):
        self.rpc_client = rpc_client
        self.options = options
        self.player = get_player(self.rpc_client, self.options.optional_player)
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

    def _choose_latest(
        self, auto_pick: bool = False
    ) -> List[Tuple["Anime", bool, List["Episode"]]]:
        with DotSpinner("Fetching status of shows in seasonals..."):
            choices = []
            for s in list(get_seasonals().seasonals.values()):
                anime = Anime.from_seasonal_entry(s)
                dub = s.dub
                episodes = anime.get_episodes(dub)
                to_watch = episodes[episodes.index(s.episode) + 1 :]
                if len(to_watch) > 0:
                    ch = Choice(
                        value=(anime, dub, to_watch),
                        name=f"{anime.name} (to watch: {len(to_watch)})",
                    )
                    choices.append(ch)
        if self.options.auto_update:
            return [ch.value for ch in choices]

        choices = inquirer.fuzzy(
            message="Select Seasonals to catch up to:",
            choices=choices,
            multiselect=True,
            long_instruction="| skip prompt: ctrl+z | toggle: ctrl+space | toggle all: ctrl+a | continue: enter |",
            mandatory=False,
            keybindings={"toggle": [{"key": "c-space"}]},
            style=get_style(
                {"long_instruction": "fg:#5FAFFF bg:#222"}, style_override=False
            ),
        ).execute()
        return choices or []

    def add_anime(self):
        # if (
        #      not self.options.no_season_search
        #      and input("Search for anime in Season? (y|n): \n>> ") == "y"
        #  ):
        #      searches = get_season_searches()
        # else:
        #     searches.append(input("Search: "))

        anime = search_show_prompt()

        if anime is None:
            return

        dub = dub_prompt(anime)

        episode = pick_episode_prompt(
            anime, dub, instruction="To start from the beginning skip this Prompt"
        )

        if episode is None:
            episode = anime.get_episodes(dub)[0]

        update_seasonal(anime, episode, dub)

        self.print_options()

    def del_anime(self):
        seasonals = list(get_seasonals().seasonals.values())

        if len(seasonals) == 0:
            error("No seasonals configured.")
            return

        entries: List[SeasonalEntry] = (
            inquirer.fuzzy(
                message="Select Seasonals to delete:",
                choices=seasonals,
                multiselect=True,
                long_instruction="| skip prompt: ctrl+z | toggle: ctrl+space | toggle all: ctrl+a | continue: enter |",
                mandatory=False,
                keybindings={"toggle": [{"key": "c-space"}]},
                style=get_style(
                    {"long_instruction": "fg:#5FAFFF bg:#222"}, style_override=False
                ),
            ).execute()
            or []
        )

        for e in entries:
            delete_seasonal(e, e.dub)

        self.print_options()

    def list_animes(self):
        for i in list(get_seasonals().seasonals.values()):
            print(i)

    def download_latest(self):
        choices = self._choose_latest()
        config = Config()
        with DotSpinner("Starting Download...") as s:
            def progress_indicator(percentage: float):
                s.set_text(f"Progress: {percentage:.1f}%")

            def info_display(message: str):
                s.write(f"> {message}")

            downloader = Downloader(progress_indicator, info_display)

            for anime, dub, eps in choices:
                for ep in eps:
                    s.set_text(
                        "Extracting streams for ",
                        colors.BLUE,
                        f"{anime.name} ({'dub' if dub else 'sub'})",
                        colors.END,
                        " Episode ",
                        ep,
                        "...",
                    )

                    stream = anime.get_video(ep, self.options.quality, dub=dub)

                    info_display(
                        f"Downloading Episode {stream.episode} of {anime.name}"
                    )
                    s.set_text("Downloading...")

                    downloader.download(
                        stream,
                        get_download_path(
                            anime, stream, parent_directory=self.dl_path
                        ),
                        container=config.remux_to,
                        ffmpeg=self.options.ffmpeg or config.ffmpeg_hls,
                    )
                    update_seasonal(anime, ep, dub)

        if not self.options.auto_update:
            self.print_options(clear_screen=True)

    def binge_latest(self):
        picked = self._choose_latest()

        for anime, dub, eps in picked:
            for e in eps:
                with DotSpinner(
                    "Extracting streams for ",
                    colors.BLUE,
                    f"{anime.name} ({'dub' if dub else 'sub'})",
                    colors.END,
                    " Episode ",
                    e,
                    "...",
                ) as s:
                    stream = anime.get_video(e, self.options.quality, dub=dub)
                    s.ok("✔")

                self.player.play_title(anime, stream)
                self.player.wait()

                update_seasonal(anime, e, dub)

        self.print_options()

    def quit(self):
        sys.exit(0)
