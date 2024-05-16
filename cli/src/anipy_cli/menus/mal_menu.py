import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Tuple

from anipy_api.anime import Anime
from anipy_api.download import Downloader
from anipy_api.mal import MALAnime, MALMyListStatusEnum, MyAnimeList
from anipy_api.provider import LanguageTypeEnum
from anipy_api.provider.base import Episode

from anipy_api.locallist import LocalList, LocalListEntry
from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.utils import get_style

from anipy_cli.arg_parser import CliArgs
from anipy_cli.colors import colors, cprint
from anipy_cli.config import Config
from anipy_cli.mal_proxy import MyAnimeListProxy
from anipy_cli.menus.base_menu import MenuBase, MenuOption
from anipy_cli.util import (
    DotSpinner,
    error,
    find_closest,
    get_configured_player,
    get_download_path,
    migrate_locallist,
)
from anipy_cli.prompts import search_show_prompt


class MALMenu(MenuBase):
    def __init__(self, mal: MyAnimeList, options: CliArgs):
        self.mal = mal
        self.mal_proxy = MyAnimeListProxy(self.mal)

        with DotSpinner("Fetching your MyAnimeList..."):
            self.mal_proxy.get_list()

        self.options = options
        self.player = get_configured_player(self.options.optional_player)
        self.seasonals_list = LocalList(
            Config()._seasonal_file_path, migrate_cb=migrate_locallist
        )

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
            MenuOption("Quit", sys.exit, "q"),
        ]

    def add_anime(self):
        self.print_options()

        query = inquirer.text(  # type: ignore
            "Search Anime:",
            long_instruction="To cancel this prompt press ctrl+z",
            mandatory=False,
        ).execute()

        if query is None:
            return

        with DotSpinner("Searching for ", colors.BLUE, query, "..."):
            results = self.mal.get_search(query)

        anime = inquirer.fuzzy(  # type: ignore
            message="Select Show:",
            choices=[Choice(value=r, name=self._format_mal_anime(r)) for r in results],
            transformer=lambda x: x.split("|")[-1].strip(),
            long_instruction="To skip this prompt press crtl+z",
            mandatory=False,
        ).execute()

        if anime is None:
            return

        anime = MALAnime.from_dict(anime)
        with DotSpinner("Adding ", colors.BLUE, anime.title, " to your MAL...") as s:
            self.mal_proxy.update_show(anime, MALMyListStatusEnum.WATCHING)
            s.ok("✔")

    def del_anime(self):
        self.print_options()
        with DotSpinner("Fetching your MAL..."):
            mylist = self.mal_proxy.get_list()

        entries = (
            inquirer.fuzzy(  # type: ignore
                message="Select Seasonals to delete:",
                choices=[
                    Choice(value=e, name=self._format_mal_anime(e)) for e in mylist
                ],
                multiselect=True,
                transformer=lambda x: [e.split("|")[-1].strip() for e in x],
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
                self.mal_proxy.delete_show(MALAnime.from_dict(e))
            s.ok("✔")

    def list_anime(self):
        with DotSpinner("Fetching your MAL..."):
            mylist = [
                self._format_mal_anime(e)
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

        inquirer.fuzzy(  # type: ignore
            message="View your List",
            choices=mylist,
            mandatory=False,
            transformer=lambda x: x.split("|")[-1].strip(),
            long_instruction="To skip this prompt press ctrl+z",
        ).execute()

        self.print_options()

    def tag_anime(self):
        with DotSpinner("Fetching your MAL..."):
            mylist = [
                Choice(value=e, name=self._format_mal_anime(e))
                for e in self.mal_proxy.get_list()
            ]

        entries = (
            inquirer.fuzzy(  # type: ignore
                message="Select Anime to change tags of:",
                choices=mylist,
                multiselect=True,
                long_instruction="| skip prompt: ctrl+z | toggle: ctrl+space | toggle all: ctrl+a | continue: enter |",
                transformer=lambda x: [e.split("|")[-1].strip() for e in x],
                mandatory=False,
                keybindings={"toggle": [{"key": "c-space"}]},
                style=get_style(
                    {"long_instruction": "fg:#5FAFFF bg:#222"}, style_override=False
                ),
            ).execute()
            or []
        )
        entries = [MALAnime.from_dict(e) for e in entries]

        if not entries:
            return

        config = Config()

        choices = []
        if config.mal_dub_tag:
            choices.append(
                Choice(
                    value=config.mal_dub_tag,
                    name=f"{config.mal_dub_tag} (sets wheter you prefer to watch a particular anime in dub)",
                )
            )

        if config.mal_ignore_tag:
            choices.append(
                Choice(
                    value=config.mal_ignore_tag,
                    name=f"{config.mal_ignore_tag} (sets wheter anipy-cli will ignore a particular anime)",
                )
            )

        if not choices:
            error("no tags to configure, check your config")
            return

        tags: List[str] = inquirer.select(  # type: ignore
            message="Select tags to add/remove:",
            choices=choices,
            multiselect=True,
            long_instruction="| skip prompt: ctrl+z | toggle: ctrl+space | toggle all: ctrl+a | continue: enter |",
            mandatory=False,
            keybindings={"toggle": [{"key": "c-space"}]},
            style=get_style(
                {"long_instruction": "fg:#5FAFFF bg:#222"}, style_override=False
            ),
        ).execute()

        if not tags:
            return

        action: str = inquirer.select(  # type: ignore
            message="Choose which Action to apply:",
            choices=["Add", "Remove"],
            long_instruction="To skip this prompt press ctrl+z",
            mandatory=False,
        ).execute()

        if not action:
            return

        for e in entries:
            if action == "Add":
                self.mal_proxy.update_show(e, tags=set(tags))
            else:
                current_tags = e.my_list_status.tags if e.my_list_status else []
                for t in tags:
                    try:
                        current_tags.remove(t)
                    except ValueError:
                        continue

                self.mal_proxy.update_show(e, tags=set(current_tags))

    def download(self, all: bool = False):
        picked = self._choose_latest(all=all)
        config = Config()
        total_eps = sum([len(e) for a, m, lang, e in picked])
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

            for anime, mal_anime, lang, eps in picked:
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
                        f"Downloading Episode {stream.episode} of {anime.name} ({lang})"
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
        total_eps = sum([len(e) for a, m, lang, e in picked])
        if total_eps == 0:
            print("Nothing to watch, returning...")
            return
        else:
            print(f"Playing a total of {total_eps} episode(s)")

        for anime, mal_anime, lang, eps in picked:
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

                self.mal_proxy.update_show(
                    mal_anime, status=MALMyListStatusEnum.WATCHING, episode=int(ep)
                )

    def manual_maps(self):
        mylist = self.mal_proxy.get_list()
        self._create_maps_mal(mylist)

    def sync_seasonals_mal(self):
        config = Config()
        seasonals = self.seasonals_list.get_all()
        mappings = self._create_maps_provider(seasonals)
        with DotSpinner("Syncing Seasonals into MyAnimeList") as s:
            for k, v in mappings.items():
                tags = set()
                if config.mal_dub_tag:
                    if k.language == LanguageTypeEnum.DUB:
                        tags.add(config.mal_dub_tag)

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
                if config.mal_dub_tag:
                    if k.my_list_status and config.mal_dub_tag in k.my_list_status.tags:
                        pref_lang = LanguageTypeEnum.DUB
                    else:
                        pref_lang = LanguageTypeEnum.SUB
                else:
                    pref_lang = (
                        LanguageTypeEnum.DUB
                        if config.preferred_type == "dub"
                        else LanguageTypeEnum.SUB
                    )

                if pref_lang in v.languages:
                    lang = pref_lang
                else:
                    lang = next(iter(v.languages))

                provider_episodes = v.get_episodes(lang)
                episode = (
                    k.my_list_status.num_episodes_watched if k.my_list_status else 0
                )

                if episode == 0:
                    episode = provider_episodes[0]
                else:
                    episode = find_closest(provider_episodes, episode)

                self.seasonals_list.update(v, episode=episode, language=lang)
            s.ok("✔")

    def _choose_latest(
        self, all: bool = False
    ) -> List[Tuple[Anime, MALAnime, LanguageTypeEnum, List[Episode]]]:
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
            choices = inquirer.fuzzy(  # type: ignore
                message="Select shows to catch up to:",
                choices=[
                    Choice(value=e, name=self._format_mal_anime(e)) for e in mylist
                ],
                multiselect=True,
                transformer=lambda x: [e.split("|")[-1].strip() for e in x],
                long_instruction="| skip prompt: ctrl+z | toggle: ctrl+space | toggle all: ctrl+a | continue: enter |",
                mandatory=False,
                keybindings={"toggle": [{"key": "c-space"}]},
                style=get_style(
                    {"long_instruction": "fg:#5FAFFF bg:#222"}, style_override=False
                ),
            ).execute()

            if choices is None:
                return []

            mylist = [MALAnime.from_dict(c) for c in choices]

        config = Config()
        to_watch: List[Tuple[Anime, MALAnime, LanguageTypeEnum, List[Episode]]] = []

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

                if config.mal_dub_tag:
                    if e.my_list_status and config.mal_dub_tag in e.my_list_status.tags:
                        pref_lang = LanguageTypeEnum.DUB
                    else:
                        pref_lang = LanguageTypeEnum.SUB
                else:
                    pref_lang = (
                        LanguageTypeEnum.DUB
                        if config.preferred_type == "dub"
                        else LanguageTypeEnum.SUB
                    )

                if pref_lang in result.languages:
                    lang = pref_lang
                    s.write(
                        f"> Looking for {lang} episodes because of config/tag preference"
                    )
                else:
                    lang = next(iter(result.languages))
                    s.write(
                        f"> Looking for {lang} episodes because your preferred type is not available"
                    )

                episodes = result.get_episodes(lang)

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

                to_watch.append((result, e, lang, will_watch))

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
            anime = search_show_prompt("mal", skip_season_search=True)
            if not anime:
                continue

            map = self.mal_proxy.map_from_mal(f, anime)
            if map is not None:
                mappings.update({f: map})

        self.print_options()
        return mappings

    def _create_maps_provider(
        self, to_map: List[LocalListEntry]
    ) -> Dict[LocalListEntry, MALAnime]:
        with DotSpinner("Starting Automapping...") as s:
            failed: List[LocalListEntry] = []
            mappings: Dict[LocalListEntry, MALAnime] = {}
            counter = 0

            def do_map(entry: LocalListEntry, to_map_length: int):
                nonlocal failed, counter
                try:
                    anime = Anime.from_local_list_entry(entry)
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
            query = inquirer.text(  # type: ignore
                "Search Anime:",
                long_instruction="To skip this prompt press ctrl+z",
                mandatory=False,
            ).execute()

            if query is None:
                continue

            with DotSpinner("Searching for ", colors.BLUE, query, "..."):
                results = self.mal.get_search(query)

            anime = inquirer.fuzzy(  # type: ignore
                message="Select Show:",
                choices=[
                    Choice(value=r, name=self._format_mal_anime(r)) for r in results
                ],
                transformer=lambda x: x.split("|")[-1].strip(),
                long_instruction="To skip this prompt press crtl+z",
                mandatory=False,
            ).execute()

            if not anime:
                continue

            anime = MALAnime.from_dict(anime)
            map = self.mal_proxy.map_from_provider(
                Anime.from_local_list_entry(f), anime
            )
            if map is not None:
                mappings.update({f: map})

        self.print_options()
        return mappings

    @staticmethod
    def _format_mal_anime(anime: MALAnime) -> str:
        config = Config()
        dub = (
            config.mal_dub_tag in anime.my_list_status.tags
            if anime.my_list_status
            else False
        )

        return "{:<9} | {:<7} | {}".format(
            (
                (
                    anime.my_list_status.status.value.capitalize().replace("_", "")
                    if anime.my_list_status.status != MALMyListStatusEnum.PLAN_TO_WATCH
                    else "Planning"
                )
                if anime.my_list_status
                else "Not Added"
            ),
            f"{anime.my_list_status.num_episodes_watched if anime.my_list_status else 0}/{anime.num_episodes}",
            f"{anime.title} {'(dub)' if dub else ''}",
        )
