from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import Levenshtein
from dataclasses_json import DataClassJsonMixin

from anipy_cli.anime import Anime
from anipy_cli.mal import MALAnime, MALMediaTypeEnum, MyAnimeList
from anipy_cli.provider import BaseProvider
from anipy_cli.provider.base import ProviderSearchResult
from anipy_cli.provider.filter import FilterCapabilities, Filters, MediaType, Season


@dataclass
class ProviderMapping(DataClassJsonMixin):
    provider: str
    identifier: str
    dub: bool


@dataclass
class MALProviderMapping(DataClassJsonMixin):
    mal_anime: MALAnime
    provider_anime: Dict[str, ProviderMapping]


def _find_best_ratio(first_set: Set[str], second_set: Set[str]) -> float:
    best_ratio = 0
    for i in first_set:
        for j in second_set:
            r = Levenshtein.ratio(i, j, processor=str.lower)
            if r > best_ratio:
                best_ratio = r
            if best_ratio == 1:
                break
        else:
            continue
        break

    return best_ratio


class MyAnimeListAdapter:
    def __init__(self, myanimelist: MyAnimeList, provider: BaseProvider) -> None:
        self.mal = myanimelist
        self.provider = provider

    def _cache_result(self, mal_anime: MALAnime, anime: Anime):
        ...

    def from_provider(
        self,
        anime: Anime,
        minimum_similarity_ratio: float = 0.8,
        use_alternative_names: bool = True,
    ) -> Optional[MALAnime]:
        results = self.mal.get_search(anime.name)
        if use_alternative_names:
            anime.get_info().alternative_names

        best_anime = None
        best_ratio = 0
        for i in results:
            titles_mal = {i.title}
            titles_provider = {anime.name}

            if use_alternative_names:
                titles_mal |= {
                    i.alternative_titles.ja,
                    i.alternative_titles.en,
                    *i.alternative_titles.synonyms,
                }

                titles_provider |= set(anime.get_info().alternative_names or [])

            ratio = _find_best_ratio(titles_mal, titles_provider)

            if ratio > best_ratio:
                best_ratio = ratio
                best_anime = i

            if best_ratio == 1:
                break

        if best_ratio >= minimum_similarity_ratio:
            return best_anime

    def from_myanimelist(
        self,
        mal_anime: MALAnime,
        minimum_similarity_ratio: float = 0.8,
        use_filters: bool = True,
        use_alternative_names: bool = True,
    ) -> Optional[Anime]:
        mal_titles = {mal_anime.title}
        if use_alternative_names:
            mal_titles |= set(
                [
                    mal_anime.title,
                    mal_anime.alternative_titles.ja,
                    mal_anime.alternative_titles.en,
                    *mal_anime.alternative_titles.synonyms,
                ]
            )

        provider_filters = Filters()
        if self.provider.FILTER_CAPS & FilterCapabilities.YEAR:
            provider_filters.year = [mal_anime.start_season.year]

        if self.provider.FILTER_CAPS & FilterCapabilities.SEASON:
            provider_filters.season = [Season[mal_anime.start_season.season.upper()]]

        if self.provider.FILTER_CAPS & FilterCapabilities.MEDIA_TYPE:
            if mal_anime.media_type != MALMediaTypeEnum.UNKNOWN:
                provider_filters.media_type = [
                    MediaType[mal_anime.media_type.value.upper()]
                ]

        results: Set[ProviderSearchResult] = set()
        for title in mal_titles:
            results |= set(self.provider.get_search(title))
            if use_filters:
                results |= set(self.provider.get_search(title, provider_filters))
        
        best_ratio = 0
        best_anime = None
        for r in results:
            anime = Anime.from_search_result(self.provider, r)
            provider_titles = {anime.name}

            if use_alternative_names:
                provider_titles |= set(anime.get_info().alternative_names or [])

            ratio = _find_best_ratio(mal_titles, provider_titles)

            if ratio > best_ratio:
                best_ratio = ratio
                best_anime = anime

            if best_ratio == 1:
                break

        if best_ratio > minimum_similarity_ratio:
            return best_anime
