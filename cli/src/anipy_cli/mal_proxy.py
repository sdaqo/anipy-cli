from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from anipy_api.anime import Anime
from anipy_api.mal import (
    MALAnime,
    MALMyListStatus,
    MALMyListStatusEnum,
    MyAnimeList,
    MyAnimeListAdapter,
)
from anipy_api.provider import LanguageTypeEnum, list_providers
from dataclasses_json import DataClassJsonMixin, config
from InquirerPy import inquirer

from anipy_cli.config import Config
from anipy_cli.util import error, get_prefered_providers


@dataclass
class ProviderMapping(DataClassJsonMixin):
    provider: str = field(metadata=config(field_name="pv"))
    name: str = field(metadata=config(field_name="na"))
    identifier: str = field(metadata=config(field_name="id"))
    languages: Set[LanguageTypeEnum] = field(metadata=config(field_name="la"))


@dataclass
class MALProviderMapping(DataClassJsonMixin):
    mal_anime: MALAnime
    mappings: Dict[str, ProviderMapping]


@dataclass
class MALLocalList(DataClassJsonMixin):
    mappings: Dict[int, MALProviderMapping]

    def write(self, user_id: int):
        config = Config()
        local_list = config._mal_local_user_list_path.with_stem(
            f"{config._mal_local_user_list_path.stem}_{user_id}"
        )
        local_list.write_text(self.to_json())

    @staticmethod
    def read(user_id: int) -> "MALLocalList":
        config = Config()
        local_list = config._mal_local_user_list_path.with_stem(
            f"{config._mal_local_user_list_path.stem}_{user_id}"
        )

        if not local_list.is_file():
            local_list.parent.mkdir(exist_ok=True, parents=True)
            local_list.touch()
            mylist = MALLocalList({})
            mylist.write(user_id)
            return mylist

        try:
            mylist: MALLocalList = MALLocalList.from_json(local_list.read_text())
        except KeyError:
            choice = inquirer.confirm(
                message=f"Your local MyAnimeList ({str(local_list)}) is not in the correct format, should it be deleted?",
                default=False,
            ).execute()
            if choice:
                local_list.unlink()
                return MALLocalList.read(user_id)
            else:
                error("could not read your MyAnimeList", fatal=True)

        return mylist


class MyAnimeListProxy:
    def __init__(self, mal: MyAnimeList):
        self.mal = mal
        self.user_id = mal.get_user().id
        self.local_list = MALLocalList.read(self.user_id)

    def _cache_list(self, mylist: List[MALAnime]):
        config = Config()
        for e in mylist:
            if self.local_list.mappings.get(e.id, None):
                if e.my_list_status and config.mal_ignore_tag in e.my_list_status.tags:
                    self.local_list.mappings.pop(e.id)
                else:
                    self.local_list.mappings[e.id].mal_anime = e
            else:
                self.local_list.mappings[e.id] = MALProviderMapping(e, {})

        self.local_list.write(self.user_id)

    def _write_mapping(self, mal_anime: MALAnime, mapping: Anime):
        self._cache_list([mal_anime])

        self.local_list.mappings[mal_anime.id].mappings[
            f"{mapping.provider.NAME}:{mapping.identifier}"
        ] = ProviderMapping(
            mapping.provider.NAME, mapping.name, mapping.identifier, mapping.languages
        )

        self.local_list.write(self.user_id)

    def get_list(
        self, status_catagories: Optional[Set[MALMyListStatusEnum]] = None
    ) -> List[MALAnime]:
        config = Config()
        mylist: List[MALAnime] = []

        catagories = (
            status_catagories
            if status_catagories is not None
            else set(
                [MALMyListStatusEnum[s.upper()] for s in config.mal_status_categories]
            )
        )

        for c in catagories:
            mylist.extend(
                filter(
                    lambda e: (
                        config.mal_ignore_tag not in e.my_list_status.tags
                        if e.my_list_status
                        else True
                    ),
                    self.mal.get_anime_list(c),
                )
            )

        self._cache_list(mylist)
        filtered_list = filter(
            lambda x: (
                x.my_list_status.status in catagories if x.my_list_status else False
            ),
            mylist,
        )
        return list(filtered_list)

    def update_show(
        self,
        anime: MALAnime,
        status: Optional[MALMyListStatusEnum] = None,
        episode: Optional[int] = None,
        tags: Set[str] = set(),
    ) -> MALMyListStatus:
        config = Config()
        tags |= set(config.mal_tags)
        result = self.mal.update_anime_list(
            anime.id, status=status, watched_episodes=episode, tags=list(tags)
        )
        anime.my_list_status = result
        self._cache_list([anime])
        return result

    def delete_show(self, anime: MALAnime) -> None:
        self.local_list.mappings.pop(anime.id)
        self.local_list.write(self.user_id)

        self.mal.remove_from_anime_list(anime.id)

    def map_from_mal(
        self, anime: MALAnime, mapping: Optional[Anime] = None
    ) -> Optional[Anime]:
        if mapping is not None:
            self._write_mapping(anime, mapping)
            return mapping

        if self.local_list.mappings[anime.id].mappings:
            map = list(self.local_list.mappings[anime.id].mappings.values())[0]
            provider = next(filter(lambda x: x.NAME == map.provider, list_providers()))
            return Anime(provider(), map.name, map.identifier, map.languages)

        config = Config()
        result = None
        for p in get_prefered_providers("mal"):
            adapter = MyAnimeListAdapter(self.mal, p)
            result = adapter.from_myanimelist(
                anime,
                config.mal_mapping_min_similarity,
                config.mal_mapping_use_filters,
                config.mal_mapping_use_alternatives,
            )

            if result is not None:
                break

        if result:
            self._write_mapping(anime, result)

        return result

    def map_from_provider(
        self, anime: Anime, mapping: Optional[MALAnime] = None
    ) -> Optional[MALAnime]:
        if mapping is not None:
            self._write_mapping(mapping, anime)
            return mapping

        for _, m in self.local_list.mappings.items():
            existing = m.mappings.get(f"{anime.provider.NAME}:{anime.identifier}", None)
            if existing:
                return m.mal_anime

        config = Config()
        adapter = MyAnimeListAdapter(self.mal, anime.provider)
        result = adapter.from_provider(
            anime,
            config.mal_mapping_min_similarity,
            config.mal_mapping_use_alternatives,
        )

        if result:
            self._write_mapping(result, anime)

        return result
