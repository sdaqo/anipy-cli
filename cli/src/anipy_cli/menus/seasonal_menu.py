import sys
from typing import TYPE_CHECKING, List, Tuple

from anipy_api.anime import Anime
from anipy_api.download import Downloader
from anipy_api.provider import LanguageTypeEnum
from anipy_api.provider.base import Episode
from anipy_api.locallist import LocalList, LocalListEntry
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.utils import get_style

from anipy_cli.colors import colors
from anipy_cli.config import Config
from anipy_cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.util import (
    DotSpinner,
    error,
    get_configured_player,
    get_download_path,
    migrate_locallist,
)
from anipy_cli.prompts import pick_episode_prompt, search_show_prompt, lang_prompt

if TYPE_CHECKING:
    from anipy_cli.arg_parser import CliArgs


class SeasonalMenu(MenuBase):
    def __init__(self, options: "CliArgs"):
        self.options = options
        self.player = get_configured_player(self.options.optional_player)

        config = Config()
        self.dl_path = config.seasonals_dl_path
        self.seasonal_list = LocalList(config._seasonal_file_path, migrate_locallist)
        if options.location:
            self.dl_path = options.location

    @property
    def menu_options(self) -> List[MenuOption]:
        return [
            MenuOption("Add Anime", self.add_anime, "a"),
            MenuOption("Delete one anime from seasonals", self.del_anime, "e"),
            MenuOption("List anime in seasonals", self.list_animes, "l"),
            MenuOption("Change dub/sub of anime in seasonals", self.change_lang, "c"),
            MenuOption("Download newest episodes", self.download_latest, "d"),
            MenuOption("Binge watch newest episodes", self.binge_latest, "w"),
            MenuOption("Quit", self.quit, "q"),
        ]

    def print_header(self):
        pass

    def _choose_latest(self) -> List[Tuple["Anime", LanguageTypeEnum, List["Episode"]]]:
        with DotSpinner("Fetching status of shows in seasonals..."):
            choices = []
            for s in self.seasonal_list.get_all():
                anime = Anime.from_local_list_entry(s)
                lang = s.language
                episodes = anime.get_episodes(lang)
                to_watch = episodes[episodes.index(s.episode) + 1 :]
                if len(to_watch) > 0:
                    ch = Choice(
                        value=(anime, lang, to_watch),
                        name=f"{anime.name} (to watch: {len(to_watch)})",
                    )
                    choices.append(ch)

        if self.options.auto_update:
            return [ch.value for ch in choices]

        choices = inquirer.fuzzy(  # type: ignore
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
        anime = search_show_prompt("default")

        if anime is None:
            return

        lang = lang_prompt(anime)

        episode = pick_episode_prompt(
            anime, lang, instruction="To start from the beginning skip this Prompt"
        )

        if episode is None:
            episode = anime.get_episodes(lang)[0]

        self.seasonal_list.update(anime, episode=episode, language=lang)

        self.print_options()

    def del_anime(self):
        seasonals = self.seasonal_list.get_all()

        if len(seasonals) == 0:
            error("No seasonals configured.")
            return

        entries: List[LocalListEntry] = (
            inquirer.fuzzy(  # type: ignore
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
            self.seasonal_list.delete(e)

        self.print_options()

    def change_lang(self):
        seasonals = self.seasonal_list.get_all()

        if len(seasonals) == 0:
            error("No seasonals configured.")
            return

        entries: List[LocalListEntry] = (
            inquirer.fuzzy(  # type: ignore
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

        if not entries:
            return

        action: str = inquirer.select(  # type: ignore
            message="Switch to:",
            choices=["Sub", "Dub"],
            long_instruction="To skip this prompt press ctrl+z",
            mandatory=False,
        ).execute()

        if not action:
            return

        for e in entries:
            if e.language == LanguageTypeEnum.DUB:
                new_lang = LanguageTypeEnum.SUB
            else:
                new_lang = LanguageTypeEnum.DUB
            if new_lang in e.languages:
                self.seasonal_list.update(e, language=new_lang)
            else:
                print(f"> {new_lang} is for {e.name} not available")

    def list_animes(self):
        for i in self.seasonal_list.get_all():
            print(i)

    def download_latest(self):
        picked = self._choose_latest()
        config = Config()
        total_eps = sum([len(e) for _a, _d, e in picked])
        if total_eps == 0:
            print("Nothing to download, returning...")
            return
        else:
            print(f"Downloading a total of {total_eps} episode(s)")
        with DotSpinner("Starting Download...") as s:

            def progress_indicator(percentage: float):
                s.set_text(f"Progress: {percentage:.1f}%")

            def info_display(message: str):
                s.write(f"> {message}")

            downloader = Downloader(progress_indicator, info_display)

            for anime, lang, eps in picked:
                for ep in eps:
                    s.set_text(
                        "Extracting streams for ",
                        colors.BLUE,
                        f"{anime.name} ({lang})",
                        colors.END,
                        " Episode ",
                        ep,
                        "...",
                    )

                    stream = anime.get_video(
                        ep, lang, preferred_quality=self.options.quality
                    )

                    info_display(
                        f"Downloading Episode {stream.episode} of {anime.name}"
                    )
                    s.set_text("Downloading...")

                    downloader.download(
                        stream,
                        get_download_path(anime, stream, parent_directory=self.dl_path),
                        container=config.remux_to,
                        ffmpeg=self.options.ffmpeg or config.ffmpeg_hls,
                    )
                    self.seasonal_list.update(anime, episode=ep, language=lang)

        if not self.options.auto_update:
            self.print_options(clear_screen=True)

    def binge_latest(self):
        picked = self._choose_latest()
        total_eps = sum([len(e) for _a, _d, e in picked])
        if total_eps == 0:
            print("Nothing to watch, returning...")
            return
        else:
            print(f"Playing a total of {total_eps} episode(s)")
        for anime, lang, eps in picked:
            for ep in eps:
                with DotSpinner(
                    "Extracting streams for ",
                    colors.BLUE,
                    f"{anime.name} ({lang})",
                    colors.END,
                    " Episode ",
                    ep,
                    "...",
                ) as s:
                    stream = anime.get_video(
                        ep, lang, preferred_quality=self.options.quality
                    )
                    s.ok("✔")

                self.player.play_title(anime, stream)
                self.player.wait()
                self.seasonal_list.update(anime, episode=ep, language=lang)

        self.print_options()

    def quit(self):
        sys.exit(0)
