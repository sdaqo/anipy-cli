import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

from InquirerPy import inquirer
from InquirerPy.utils import get_style

from anipy_api.anime import Anime
from anipy_cli.arg_parser import CliArgs
from anipy_cli.colors import colors, cprint
from anipy_cli.mal_proxy import MyAnimeListProxy
from anipy_cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.util import (
    DotSpinner,
    find_closest,
    get_download_path,
    search_show_prompt,
    error,
    get_configured_player
)
from anipy_cli.config import Config
from anipy_api.download import Downloader
from anipy_api.mal import MALAnime, MALMyListStatusEnum, MyAnimeList
from anipy_api.provider.base import Episode
from anipy_api.seasonal import SeasonalEntry, get_seasonals, update_seasonal


class MALMenu(MenuBase):
    def __init__(self, mal: MyAnimeList, options: CliArgs, rpc_client=None):
        self.mal = mal
        self.mal_proxy = MyAnimeListProxy(self.mal)

        with DotSpinner("Fetching your MyAnimeList..."):
            self.mal_proxy.get_list()

        self.options = options
        self.rpc_client = rpc_client
        self.player = get_configured_player(self.rpc_client, self.options.optional_player)

        self.dl_path = Config().seasonals_dl_path
        if options.location:
            self.dl_path = options.location

    def print_header(self):
        pass

    @property
    def menu_options(self) -> List[MenuOption]:
        return [
            MenuOption("Add Anime", self.add_anime, "a"),
            MenuOption("Delete one anime from MyAnimeList", self.del_anime, "e"),
            MenuOption("List anime in MyAnimeList", self.list_anime, "l"),
            MenuOption("Tag anime in MyAnimeList (dub/ignore)", self.tag_anime, "t"),
            MenuOption("Map MyAnimeList anime to providers", self.manual_maps, "m"),
            MenuOption("Sync MyAnimeList into seasonals", self.sync_mal_seasonls, "s"),
            MenuOption("Sync seasonals into MyAnimeList", self.sync_seasonals_mal, "b"),
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

    def list_anime(self):
        with DotSpinner("Fetching your MAL..."):
            mylist = [
                "{:<9} | {:<7} | {}".format(
                    (
                        e.my_list_status.status.value.capitalize().replace("_", "")
                        if e.my_list_status.status != MALMyListStatusEnum.PLAN_TO_WATCH
                        else "Planning"
                    ),
                    f"{e.my_list_status.num_episodes_watched}/{e.num_episodes}",
                    e.title,
                )
                for e in self.mal_proxy.get_list(
                    status_catagories=set(
                        [
                            MALMyListStatusEnum.WATCHING,
                            MALMyListStatusEnum.COMPLETED,
                            MALMyListStatusEnum.ON_HOLD,
                            MALMyListStatusEnum.PLAN_TO_WATCH,
                            MALMyListStatusEnum.DROPPED,
                        ]
                    )
                )
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

    def tag_anime(self): ...

    def download(self, all: bool = False):
        picked = self._choose_latest(all=all)
        config = Config()
        total_eps = sum([len(e) for a, m, d, e in picked])
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
                        f"Downloading Episode {stream.episode} of {anime.name} ({'dub' if dub else 'sub'})"
                    )
                    s.set_text("Downloading...")

                    downloader.download(
                        stream,
                        get_download_path(anime, stream, parent_directory=self.dl_path),
                        container=config.remux_to,
                        ffmpeg=self.options.ffmpeg or config.ffmpeg_hls,
                    )
                    if not all:
                        self.mal_proxy.update_show(
                            mal_anime,
                            status=MALMyListStatusEnum.WATCHING,
                            episode=int(ep),
                        )

    def binge_latest(self):
        picked = self._choose_latest()
        total_eps = sum([len(e) for a, m, d, e in picked])
        if total_eps == 0:
            print("Nothing to watch, returning...")
            return
        else:
            print(f"Playing a total of {total_eps} episode(s)")

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

    def manual_maps(self):
        mylist = self.mal_proxy.get_list()
        self._create_maps_mal(mylist)

    def sync_seasonals_mal(self):
        config = Config()
        seasonals = get_seasonals(config._seasonal_file_path).seasonals.values()
        mappings = self._create_maps_provider(list(seasonals))
        with DotSpinner("Syncing Seasonals into MyAnimeList") as s:
            for k, v in mappings.items():
                tags = set()
                if config.mal_dub_tag:
                    if k.dub:
                        tags |= config.mal_dub_tag

                if v.my_list_status:
                    if config.mal_ignore_tag in v.my_list_status.tags:
                        continue
                    tags |= set(v.my_list_status.tags)

                self.mal_proxy.update_show(
                    v,
                    status=MALMyListStatusEnum.WATCHING,
                    episode=int(k.episode),
                    tags=tags,
                )
            s.ok("✔")

    def sync_mal_seasonls(self):
        config = Config()
        mylist = self.mal_proxy.get_list()
        mappings = self._create_maps_mal(mylist)
        with DotSpinner("Syncing MyAnimeList into Seasonals") as s:
            for k, v in mappings.items():
                provider_episodes = v.get_episodes()
                episode = (
                    k.my_list_status.num_episodes_watched if k.my_list_status else 0
                )
                if v.has_dub:
                    if not config.mal_dub_tag:
                        dub = config.preferred_type == "dub"
                    elif (
                        k.my_list_status and config.mal_dub_tag in k.my_list_status.tags
                    ):
                        dub = True
                    else:
                        dub = False
                else:
                    dub = False

                if episode == 0:
                    episode = provider_episodes[0]
                else:
                    episode = find_closest(provider_episodes, episode)

                update_seasonal(config._seasonal_file_path, v, episode, dub)
            s.ok("✔")

    def _choose_latest(
        self, all: bool = False
    ) -> List[Tuple[Anime, MALAnime, bool, List[Episode]]]:
        cprint(
            colors.GREEN,
            "Hint: ",
            colors.END,
            "you can fine-tune mapping behaviour in your settings!",
        )
        with DotSpinner("Fetching your MAL..."):
            mylist = self.mal_proxy.get_list()

        for i, e in enumerate(mylist):
            if e.my_list_status is None:
                mylist.pop(i)
                continue

            if e.my_list_status.num_episodes_watched == e.num_episodes:
                mylist.pop(i)

        if not (all or self.options.auto_update):
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

        with DotSpinner("Fetching episodes...") as s:
            for e in mylist:
                s.write(f"> Checking out episodes of {e.title}")

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
                    if not config.mal_dub_tag:
                        dub = config.preferred_type == "dub"
                    elif (
                        e.my_list_status and config.mal_dub_tag in e.my_list_status.tags
                    ):
                        dub = True
                    else:
                        dub = False
                else:
                    dub = False

                if dub:
                    s.write("> Looking for dub episodes because of config preference")
                episodes = result.get_episodes(dub=dub)

                will_watch = []
                if all:
                    will_watch.extend(episodes)
                else:
                    for ep in episodes_to_watch:
                        try:
                            idx = episodes.index(ep)
                            will_watch.append(episodes[idx])
                        except ValueError:
                            s.write(
                                f"> Episode {ep} not found in provider, skipping..."
                            )

                to_watch.append((result, e, dub, will_watch))

            s.ok("✔")

        return to_watch

    def _create_maps_mal(self, to_map: List[MALAnime]) -> Dict[MALAnime, Anime]:
        cprint(
            colors.GREEN,
            "Hint: ",
            colors.END,
            "you can fine-tune mapping behaviour in your settings!",
        )
        with DotSpinner("Starting Automapping...") as s:
            failed: List[MALAnime] = []
            mappings: Dict[MALAnime, Anime] = {}
            counter = 0

            def do_map(anime: MALAnime, to_map_length: int):
                nonlocal failed, counter
                try:
                    result = self.mal_proxy.map_from_mal(anime)
                    if result is None:
                        failed.append(anime)
                        s.write(f"> Failed to map {anime.id} ({anime.title})")
                    else:
                        mappings.update({anime: result})
                        s.write(
                            f"> Successfully mapped {anime.id} to {result.identifier}"
                        )

                    counter += 1
                    s.set_text(f"Progress: {counter / to_map_length * 100:.1f}%")
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
            return mappings

        for f in failed:
            cprint("Manually mapping ", colors.BLUE, f.title)
            anime = search_show_prompt()
            if not anime:
                continue

            map = self.mal_proxy.map_from_mal(f, anime)
            if map is not None:
                mappings.update({f: map})

        self.print_options()
        return mappings

    def _create_maps_provider(
        self, to_map: List[SeasonalEntry]
    ) -> Dict[SeasonalEntry, MALAnime]:
        with DotSpinner("Starting Automapping...") as s:
            failed: List[SeasonalEntry] = []
            mappings: Dict[SeasonalEntry, MALAnime] = {}
            counter = 0

            def do_map(entry: SeasonalEntry, to_map_length: int):
                nonlocal failed, counter
                try:
                    anime = Anime.from_seasonal_entry(entry)
                    result = self.mal_proxy.map_from_provider(anime)
                    if result is None:
                        failed.append(entry)
                        s.write(f"> Failed to map {anime.identifier} ({anime.name})")
                    else:
                        mappings.update({entry: result})
                        s.write(
                            f"> Successfully mapped {anime.identifier} to {result.id}"
                        )

                    counter += 1
                    s.set_text(f"Progress: {counter / to_map_length * 100}%")
                except:
                    failed.append(entry)

            with ThreadPoolExecutor(max_workers=5) as pool:
                futures = [pool.submit(do_map, a, len(to_map)) for a in to_map]
                try:
                    for future in as_completed(futures):
                        future.result()
                except KeyboardInterrupt:
                    pool.shutdown(wait=False, cancel_futures=True)
                    raise

        if not failed or self.options.auto_update or self.options.mal_sync_seasonals:
            self.print_options()
            print("Everything is mapped")
            return mappings

        for f in failed:
            cprint("Manually mapping ", colors.BLUE, f.name)
            query = inquirer.text(
                "Search Anime:",
                long_instruction="To cancel this prompt press ctrl+z",
                mandatory=False,
            ).execute()

            if query is None:
                continue

            with DotSpinner("Searching for ", colors.BLUE, query, "..."):
                results = self.mal.get_search(query)

            anime: MALAnime = inquirer.fuzzy(
                message="Select Show:",
                choices=results,
                long_instruction="To skip this prompt press crtl+z",
                mandatory=False,
            ).execute()

            if not anime:
                continue

            map = self.mal_proxy.map_from_provider(Anime.from_seasonal_entry(f), anime)
            if map is not None:
                mappings.update({f: map})

        self.print_options()
        return mappings

    def quit(self):
        sys.exit(0)
