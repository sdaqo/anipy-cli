import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Union

from InquirerPy import inquirer
from InquirerPy.utils import get_style

from anipy_cli.anime import Anime
from anipy_cli.cli.arg_parser import CliArgs
from anipy_cli.cli.colors import colors, cprint
from anipy_cli.cli.mal_proxy import MyAnimeListProxy
from anipy_cli.cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.cli.util import (
    DotSpinner,
    error,
    get_download_path,
    # get_season_searches,
    search_show_prompt,
)

from anipy_cli.config import Config
from anipy_cli.download import Downloader
from anipy_cli.mal import MALAnime, MALMyListStatusEnum, MyAnimeList
from anipy_cli.player import get_player
from anipy_cli.provider.base import Episode


class MALMenu(MenuBase):
    def __init__(self, mal: MyAnimeList, options: CliArgs, rpc_client=None):
        self.mal = mal
        self.mal_proxy = MyAnimeListProxy(self.mal)

        with DotSpinner("Fetching your MyAnimeList..."):
            self.mal_proxy.get_list()

        self.options = options
        self.rpc_client = rpc_client
        self.player = get_player(self.rpc_client, self.options.optional_player)

        self.dl_path = Config().seasonals_dl_path
        if options.location:
            self.dl_path = options.location

    def print_header(self):
        pass

    @property
    def menu_options(self) -> List[MenuOption]:
        return [
            MenuOption("Add Anime", self.add_anime, "a"),
            MenuOption("Delete one anime from mal list", self.del_anime, "e"),
            MenuOption("List anime in mal list", self.list_animes, "l"),
            MenuOption("Map MAL anime to gogo Links", self.manual_maps, "m"),
            # MenuOption("Sync MAL list into seasonals", self.sync_mal_to_seasonals, "s"),
            # MenuOption(
            #     "Sync seasonals into MAL list",
            #     self.m_class.sync_seasonals_with_mal,
            #     "b",
            # ),
            MenuOption(
                "Download newest episodes", lambda: self.download(all=False), "d"
            ),
            MenuOption("Download all episodes", lambda: self.download(all=True), "x"),
            MenuOption("Binge watch newest episodes", self.binge_latest, "w"),
            MenuOption("Quit", self.quit, "q"),
        ]

    def add_anime(self):
        # searches = []
        # if (
        #     not self.options.no_season_search
        #     and input("Search for anime in Season? (y|n): \n>> ") == "y"
        # ):
        #     searches = get_season_searches(gogo=False)
        #
        # else:
        #     searches.append(input("Search: "))
        #
        # for search in searches:
        #     if isinstance(search, dict):
        #         mal_entry = search
        #
        #     else:
        #         print("\nCurrent: ", search)
        #         temp_search = self.m_class.get_anime(search)
        #         names = [item["node"]["title"] for item in temp_search]
        #         print_names(names)
        #         selected = False
        #         skip = False
        #         while selected is False:
        #             try:
        #                 sel_index = input("Select show (Number or c for cancel):\n")
        #                 if sel_index == "c":
        #                     skip = True
        #                     break
        #                 selected = int(sel_index) - 1
        #             except ValueError:
        #                 print("Please enter a valid number.")
        #         if skip:
        #             continue
        #         mal_entry = temp_search[selected]
        #
        #     self.m_class.update_anime_list(
        #         mal_entry["node"]["id"], {"status": "watching"}
        #     )
        #     self.create_gogo_maps()
        #
        # self.print_options()
        self.print_options()

        query = inquirer.text(
            "Search Anime:",
            long_instruction="To cancel this prompt press ctrl+z",
            mandatory=False,
        ).execute()

        if query is None:
            return

        with DotSpinner("Searching for ", colors.BLUE, query, "..."):
            results = self.mal.get_search(query)

        anime: MALAnime = inquirer.fuzzy(
            message="Select Show:",
            choices=results,
            long_instruction="To skip this prompt press crtl+z",
            mandatory=False,
        ).execute()

        if anime is None:
            return

        with DotSpinner("Adding ", colors.BLUE, anime.title, "to your MAL...") as s:
            self.mal_proxy.update_show(anime, MALMyListStatusEnum.WATCHING)
            s.ok("✔")

    def del_anime(self):
        self.print_options()
        with DotSpinner("Fetching your MAL..."):
            mylist = self.mal_proxy.get_list()

        entries: List[MALAnime] = (
            inquirer.fuzzy(
                message="Select Seasonals to delete:",
                choices=mylist,
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

        with DotSpinner("Deleting anime from your MAL...") as s:
            for e in entries:
                self.mal_proxy.delete_show(e)
            s.ok("✔")

    def list_animes(self):
        with DotSpinner("Fetching your MAL..."):
            mylist = [
                "{} | {}/{} | {}".format(
                    e.my_list_status.status.value.capitalize(),
                    e.my_list_status.num_episodes_watched,
                    e.num_episodes,
                    e.title,
                )
                for e in self.mal_proxy.get_list()
                if e.my_list_status
            ]

        if not mylist:
            error("your list is empty")
            return

        inquirer.fuzzy(
            message="View your List",
            choices=mylist,
            long_instruction="To skip this prompt press ctrl+z",
        ).execute()

        self.print_options()

    def download(self, all: bool = False):
        picked = self._choose_latest(all=all)
        config = Config()
        with DotSpinner("Starting Download...") as s:

            def progress_indicator(percentage: float):
                s.set_text(f"Progress: {percentage:.1f}%")

            def info_display(message: str):
                s.write(f"> {message}")

            downloader = Downloader(progress_indicator, info_display)

            for anime, mal_anime, dub, eps in picked:
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
                        get_download_path(anime, stream, parent_directory=self.dl_path),
                        container=config.remux_to,
                        ffmpeg=self.options.ffmpeg or config.ffmpeg_hls,
                    )
                    self.mal_proxy.update_show(
                        mal_anime, status=MALMyListStatusEnum.WATCHING, episode=int(ep)
                    )

    def binge_latest(self):
        picked = self._choose_latest()

        for anime, mal_anime, dub, eps in picked:
            for ep in eps:
                with DotSpinner(
                    "Extracting streams for ",
                    colors.BLUE,
                    f"{anime.name} ({'dub' if dub else 'sub'})",
                    colors.END,
                    " Episode ",
                    ep,
                    "...",
                ) as s:
                    stream = anime.get_video(ep, self.options.quality, dub=dub)
                    s.ok("✔")

                self.player.play_title(anime, stream)
                self.player.wait()

                self.mal_proxy.update_show(
                    mal_anime, status=MALMyListStatusEnum.WATCHING, episode=int(ep)
                )

    # def sync_mal_to_seasonals(self):
    #     self.create_gogo_maps()
    #
    #     self.m_class.sync_mal_with_seasonal()

    def manual_maps(self):
        mylist = self.mal_proxy.get_list()
        self._create_maps_mal(mylist)

    def _choose_latest(
        self, all: bool = False
    ) -> List[Tuple[Anime, MALAnime, bool, List[Episode]]]:
        with DotSpinner("Fetching your MAL..."):
            mylist = self.mal_proxy.get_list()
        for i, e in enumerate(mylist):
            if e.my_list_status is None:
                mylist.pop(i)
                continue

            if e.my_list_status.num_episodes_watched == e.num_episodes:
                mylist.pop(i)

        if not all or self.options.auto_update:
            choices = inquirer.fuzzy(
                message="Select shows to catch up to:",
                choices=mylist,
                multiselect=True,
                long_instruction="| skip prompt: ctrl+z | toggle: ctrl+space | toggle all: ctrl+a | continue: enter |",
                mandatory=False,
                keybindings={"toggle": [{"key": "c-space"}]},
                style=get_style(
                    {"long_instruction": "fg:#5FAFFF bg:#222"}, style_override=False
                ),
            ).execute()

            if choices is None:
                return []

            mylist = list(choices)

        config = Config()
        to_watch: List[Tuple[Anime, MALAnime, bool, List[Episode]]] = []

        with DotSpinner("Fetching latest episodes...") as s:
            for e in mylist:
                s.write(f"> Checking out latest episodes of {e.title}")

                episodes_to_watch = list(
                    range(e.my_list_status.num_episodes_watched + 1, e.num_episodes + 1)  # type: ignore
                )

                result = self.mal_proxy.map_from_mal(e)

                if result is None:
                    s.write(
                        f"> No mapping found for {e.title} please use the `m` option to map it"
                    )
                    continue

                if result.has_dub:
                    s.write("> Looking for dub episodes because of config preference")
                    episodes = result.get_episodes(config.preferred_type == "dub")
                    dub = True
                else:
                    episodes = result.get_episodes()
                    dub = False

                will_watch = []
                for ep in episodes_to_watch:
                    try:
                        idx = episodes.index(ep)
                        will_watch.append(episodes[idx])
                    except ValueError:
                        s.write(f"> Episode {ep} not found in provider, skipping...")

                to_watch.append((result, e, dub, will_watch))

            s.ok("✔")

        return to_watch

    def _create_maps_mal(self, to_map: List[MALAnime]) -> List[Anime]:
        with DotSpinner("Starting Automapping...") as s:
            mapped: List[Anime] = []
            failed: List[MALAnime] = []
            counter = 0

            def do_map(anime: MALAnime, to_map_length: int):
                nonlocal failed, counter
                try:
                    result = self.mal_proxy.map_from_mal(anime)
                    if result is None:
                        failed.append(anime)
                        s.write(f"> Failed to map {anime.id} ({anime.title})")
                    else:
                        mapped.append(result)
                        s.write(
                            f"> Successfully mapped {anime.id} to {result.identifier}"
                        )

                    counter += 1
                    s.set_text(f"Progress: {counter / to_map_length * 100}%")
                except:
                    failed.append(anime)

            with ThreadPoolExecutor(max_workers=5) as pool:
                futures = [pool.submit(do_map, a, len(to_map)) for a in to_map]
                try:
                    for future in as_completed(futures):
                        future.result()
                except KeyboardInterrupt:
                    pool.shutdown(wait=False, cancel_futures=True)
                    raise

        if not failed or self.options.auto_update:
            self.print_options()
            print("Everything is mapped")
            return mapped

        for f in failed:
            cprint("Manually mapping ", colors.BLUE, f.title)
            anime = search_show_prompt()
            if not anime:
                continue

            map = self.mal_proxy.map_from_mal(f, anime)
            if map is not None:
                mapped.append(map)

        return mapped

    def _create_maps_provider(self, to_map: List[Union[Anime, MALAnime]]): ...

    def quit(self):
        sys.exit(0)
