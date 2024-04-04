from typing import TYPE_CHECKING, List
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.utils import get_style

from anipy_cli.cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.cli.util import DotSpinner, pick_episode_prompt, search_show_prompt
from anipy_cli.cli.colors import colors
from anipy_cli.config import Config
from anipy_cli.misc import error
from anipy_cli.player import get_player
from anipy_cli.seasonal import (
    delete_seasonal,
    get_seasonals,
    update_seasonal,
)
from anipy_cli.anime import Anime

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs

class SeasonalMenu(MenuBase):
    def __init__(self, options: 'CliArgs', rpc_client=None):
        self.rpc_client = rpc_client
        self.options = options
        self.entry = Entry()
        self.dl_path = Config().seasonals_dl_path
        self.player = get_player(self.rpc_client, self.options.optional_player)
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

    def _choose_latest(self) -> List[Choice]:
        with DotSpinner("Fetching status of shows in seasonals..."):
            choices = []
            for s in list(get_seasonals().seasonals.values()):
                anime = Anime.from_seasonal_entry(s)
                episodes = anime.get_episodes()
                to_watch = episodes[episodes.index(s.episode) + 1 :]
                if len(to_watch) > 0:
                    ch = Choice(
                        value=(anime, to_watch),
                        name=f"{anime.name} (to watch: {len(to_watch)})",
                    )
                    choices.append(ch)

        return choices

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

        episode = pick_episode_prompt(
            anime, instruction="To start from the beginning skip this Prompt"
        )

        if episode is None:
            episode = anime.get_episodes()[0]

        update_seasonal(anime, episode)

        self.print_options()

    def del_anime(self):
        seasonals = list(get_seasonals().seasonals.values())
        if len(seasonals) == 0:
            error("No seasonals configured.")
            return

        style = get_style(
            {"long_instruction": "fg:#5FAFFF bg:#222"}, style_override=False
        )
        entries = (
            inquirer.fuzzy(
                message="Select Seasonals to delete:",
                choices=seasonals,
                multiselect=True,
                long_instruction="| skip prompt: ctrl+z | toggle: ctrl+space | toggle all: ctrl+a | continue: enter |",
                mandatory=False,
                keybindings={"toggle": [{"key": "c-space"}]},
                style=style,
            ).execute()
            or []
        )

        for e in entries:
            delete_seasonal(e)

        self.print_options()

    def list_animes(self):
        for i in list(get_seasonals().seasonals.values()):
            print(i)

        style = get_style(
            {"long_instruction": "fg:#5FAFFF bg:#222"}, style_override=False
        )
        return (
            inquirer.fuzzy(
                message="Select Seasonals to catch up to:",
                choices=choices,
                multiselect=True,
                long_instruction="| skip prompt: ctrl+z | toggle: ctrl+space | toggle all: ctrl+a | continue: enter |",
                mandatory=False,
                keybindings={"toggle": [{"key": "c-space"}]},
                style=style,
            ).execute()
            or []
        )

    def download_latest(self):
        choices = self._choose_latest()
        ...
        # def progress_indicator():
        #
        # downloader = Downloader()

    def binge_latest(self):
        picked = self._choose_latest()

        for anime, eps in picked:
            for e in eps:
                with DotSpinner(
                    "Extracting streams for ",
                    colors.BLUE,
                    anime.name,
                    colors.END,
                    " Episode ",
                    e,
                    "...",
                ) as s:
                    stream = anime.get_video(e, self.options.quality)
                    s.ok("✔")

                self.player.play_title(anime, stream)
                self.player.wait()

                update_seasonal(anime, e)

        self.print_options()
