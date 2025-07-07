from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from anipy_api.anime import Anime
from anipy_api.anilist import (
    AniListAnime,
    AniListMyListStatus,
    AniListMyListStatusEnum,
    AniList,
    AniListAdapter,
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
class AniListProviderMapping(DataClassJsonMixin):
    anilist_anime: AniListAnime
    mappings: Dict[str, ProviderMapping]


@dataclass
class AniListLocalList(DataClassJsonMixin):
    mappings: Dict[int, AniListProviderMapping]

    def write(self, user_id: int):
        config = Config()
        local_list = config._anilist_local_user_list_path.with_stem(
            f"{config._anilist_local_user_list_path.stem}_{user_id}"
        )
        local_list.write_text(self.to_json())

    @staticmethod
    def read(user_id: int) -> "AniListLocalList":
        config = Config()
        local_list = config._anilist_local_user_list_path.with_stem(
            f"{config._anilist_local_user_list_path.stem}_{user_id}"
        )

        if not local_list.is_file():
            local_list.parent.mkdir(exist_ok=True, parents=True)
            local_list.touch()
            mylist = AniListLocalList({})
            mylist.write(user_id)
            return mylist

        try:
            mylist: AniListLocalList = AniListLocalList.from_json(local_list.read_text())
        except KeyError:
            choice = inquirer.confirm(
                message=f"Your local AniList ({str(local_list)}) is not in the correct format, should it be deleted?",
                default=False,
            ).execute()
            if choice:
                local_list.unlink()
                return AniListLocalList.read(user_id)
            else:
                error("could not read your AniList", fatal=True)

        return mylist


class AniListProxy:
    def __init__(self, anilist: AniList):
        self.anilist = anilist
        self.user_id = anilist.get_user().id
        self.local_list = AniListLocalList.read(self.user_id)

    def _cache_list(self, mylist: List[AniListAnime]):
        config = Config()
        for e in mylist:
            if self.local_list.mappings.get(e.id, None):
                if e.my_list_status and config.tracker_ignore_tag in e.my_list_status.tags:
                    self.local_list.mappings.pop(e.id)
                else:
                    self.local_list.mappings[e.id].anilist_anime = e
            else:
                self.local_list.mappings[e.id] = AniListProviderMapping(e, {})

        self.local_list.write(self.user_id)

    def _write_mapping(self, anilist_anime: AniListAnime, mapping: Anime):
        self._cache_list([anilist_anime])

        self.local_list.mappings[anilist_anime.id].mappings[
            f"{mapping.provider.NAME}:{mapping.identifier}"
        ] = ProviderMapping(
            mapping.provider.NAME, mapping.name, mapping.identifier, mapping.languages
        )

        self.local_list.write(self.user_id)

    def get_list(
        self, status_catagories: Optional[Set[AniListMyListStatusEnum]] = None
    ) -> List[AniListAnime]:
        config = Config()
        mylist: List[AniListAnime] = []

        catagories = (
            status_catagories
            if status_catagories is not None
            else set(
                [AniListMyListStatusEnum[s.upper()] for s in config.tracker_status_categories]
            )
        )

        for c in catagories:
            mylist.extend(
                filter(
                    lambda e: (
                        config.tracker_ignore_tag not in e.my_list_status.tags
                        if e.my_list_status
                        else True
                    ),
                    self.anilist.get_anime_list(c),
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
        anime: AniListAnime,
        status: Optional[AniListMyListStatusEnum] = None,
        episode: Optional[int] = None,
        tags: Set[str] = set(),
    ) -> AniListMyListStatus:
        config = Config()
        tags |= set(config.tracker_tags)
        result = self.anilist.update_anime_list(
            anime.id, status=status, watched_episodes=episode, tags=list(tags)
        )
        anime.my_list_status = result
        self._cache_list([anime])
        return result

    def delete_show(self, anime: AniListAnime) -> None:
        self.local_list.mappings.pop(anime.id)
        self.local_list.write(self.user_id)

        self.anilist.remove_from_anime_list(anime.id)

    def map_from_anilist(
        self, anime: AniListAnime, mapping: Optional[Anime] = None
    ) -> Optional[Anime]:
        if mapping is not None:
            self._write_mapping(anime, mapping)
            return mapping

        if self.local_list.mappings[anime.id].mappings:
            for map in self.local_list.mappings[anime.id].mappings.values():
                provider = next(
                    filter(lambda x: x.NAME == map.provider, list_providers()), None
                )

                if provider is None:
                    continue

                return Anime(provider(), map.name, map.identifier, map.languages)

        config = Config()
        result = None
        for p in get_prefered_providers("anilist"):
            adapter = AniListAdapter(self.anilist, p)
            result = adapter.from_anilist(
                anime,
                config.tracker_mapping_min_similarity,
                config.tracker_mapping_use_filters,
                config.tracker_mapping_use_alternatives,
            )
            if result is not None:
                break

        if result:
            self._write_mapping(anime, result)

        return result

    def map_from_provider(
        self, anime: Anime, mapping: Optional[AniListAnime] = None
    ) -> Optional[AniListAnime]:
        if mapping is not None:
            self._write_mapping(mapping, anime)
            return mapping

        for _, m in self.local_list.mappings.items():
            existing = m.mappings.get(f"{anime.provider.NAME}:{anime.identifier}", None)
            if existing:
                return m.anilist_anime

        config = Config()
        adapter = AniListAdapter(self.anilist, anime.provider)
        result = adapter.from_provider(
            anime,
            config.tracker_mapping_min_similarity,
            config.tracker_mapping_use_alternatives,
        )

        if result:
            self._write_mapping(result, anime)

        return result
