import datetime
import Levenshtein
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Set

from dataclasses_json import DataClassJsonMixin, Undefined
from requests import Request, Session

from anipy_cli.error import MyAnimeListError
from anipy_cli.version import __appname__, __version__
from anipy_cli.anime import Anime
from anipy_cli.provider import ProviderSearchResult, FilterCapabilities, Filters, MediaType, Season

if TYPE_CHECKING:
    from anipy_cli.provider import BaseProvider

class MALMyListStatusEnum(Enum):
    WATCHING = "watching"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    DROPPED = "dropped"
    PLAN_TO_WATCH = "plan_to_watch"


class MALMediaTypeEnum(Enum):
    TV = "tv"
    MOVIE = "movie"
    OVA = "ova"
    ONA = "ona"
    SPECIAL = "special"
    MUSIC = "music"
    UNKNOWN = "unknown"


@dataclass
class MALMyListStatus(DataClassJsonMixin):
    num_episodes_watched: int
    tags: List[str]
    status: MALMyListStatusEnum
    score: int


@dataclass
class MALAlternativeTitles(DataClassJsonMixin):
    en: str
    ja: str
    synonyms: List[str]


@dataclass
class MALSeason(DataClassJsonMixin):
    season: str
    year: int


@dataclass
class MALAnime(DataClassJsonMixin):
    id: int
    title: str
    media_type: MALMediaTypeEnum
    alternative_titles: MALAlternativeTitles
    start_season: MALSeason
    my_list_status: Optional[MALMyListStatus] = None


@dataclass
class MALPaging(DataClassJsonMixin):
    previous: Optional[str] = None
    next: Optional[str] = None


@dataclass
class MALResourceNode(DataClassJsonMixin):
    node: MALAnime


@dataclass
class MALPagingResource(DataClassJsonMixin):
    data: List[MALResourceNode]
    paging: MALPaging


class MyAnimeList:
    API_BASE = "https://api.myanimelist.net/v2"
    CLIENT_ID = "6114d00ca681b7701d1e15fe11a4987e"

    # Corresponds to fields of MALAnime object
    RESPONSE_FIELDS = [
        "id",
        "title",
        "alternative_titles",
        "start_season",
        "media_type",
        "my_list_status{tags,num_episodes_watched,score,status}",
    ]

    @staticmethod
    def from_password_grant(
        user: str, password: str, client_id: Optional[str] = None
    ) -> "MyAnimeList":
        mal = MyAnimeList(client_id)
        mal._refresh_auth(user, password)
        return mal

    @staticmethod
    def from_rt_grant(
        refresh_token: str, client_id: Optional[str] = None
    ) -> "MyAnimeList":
        mal = MyAnimeList(client_id)
        mal._refresh_token = refresh_token
        mal._refresh_auth()
        return mal

    def __init__(self, client_id: Optional[str] = None):
        if client_id:
            self.CLIENT_ID = client_id

        self._refresh_token = None
        self._auth_expire_time = datetime.datetime.min

        self._session = Session()
        self._session.headers.update(
            {
                "X-MAL-Client-ID": self.CLIENT_ID,
                "User-Agent": f"{__appname__}/{__version__}",
            }
        )

    def get_search(self, query: str, limit: int = 20, pages: int = 1) -> List[MALAnime]:
        return self._get_resource("anime", {"q": query}, limit, pages)
    
    def get_anime(self, anime_id: int) -> MALAnime:
        request = Request("GET", f"{self.API_BASE}/anime/{anime_id}")
        return MALAnime.from_json(self._make_request(request))

    def get_anime_list(
        self, status_filter: Optional[MALMyListStatusEnum] = None
    ) -> List[MALAnime]:
        params = dict()
        if status_filter:
            params = {"status": status_filter.value}

        return self._get_resource("users/@me/animelist", params, limit=20, pages=-1)

    def update_anime_list(
        self,
        anime_id: int,
        status: Optional[MALMyListStatusEnum] = None,
        watched_episodes: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> MALMyListStatus:
        request = Request("PATCH", f"{self.API_BASE}/anime/{anime_id}/my_list_status")
        request.params.update(
            {
                k: v
                for k, v in {
                    "status": status,
                    "num_watched_episode": watched_episodes,
                    "tags": tags,
                }.items()
                if v
            }
        )

        return MALMyListStatus.schema(unknown=Undefined.EXCLUDE).loads(
            self._make_request(request)
        )[0]

    def delete_from_anime_list(self, anime_id: int):
        request = Request("DELETE", f"{self.API_BASE}/anime/{anime_id}/my_list_status")
        self._make_request(request)

    def _get_resource(
        self, resource: str, params: dict, limit: int, pages: int
    ) -> List[MALAnime]:
        request = Request("GET", f"{self.API_BASE}/{resource}", params=params)
        request.params["fields"] = ",".join(self.RESPONSE_FIELDS)

        next_page = True
        offset = 0
        anime_list = []

        while next_page:
            request.params.update({"limit": limit, "offset": offset})
            response = MALPagingResource.from_json(self._make_request(request))

            if response.paging.next:
                offset += limit
                pages -= 1
            else:
                next_page = False

            anime_list.extend([i.node for i in response.data])

            if pages == 0:
                next_page = False

        return anime_list

    def _make_request(self, request: Request) -> str:
        prepped = request.prepare()
        prepped.headers.update(self._session.headers)  # type: ignore

        response = self._session.send(prepped)

        if response.ok:
            return response.text

        if response.status_code == 401:
            self._refresh_auth()
            return self._make_request(request)

        raise MyAnimeListError(response.url, response.status_code, response.json())

    def _refresh_auth(self, user: Optional[str] = None, password: Optional[str] = None):
        time_now = datetime.datetime.now()
        if self._auth_expire_time > time_now:
            return True

        if user and password:
            grant_type = "password"
            url = "https://api.myanimelist.net/v2/auth/token"
            data = {
                "client_id": self.CLIENT_ID,
                "grant_type": grant_type,
                "password": password,
                "username": user,
            }
        else:
            grant_type = "refresh_token"
            url = "https://myanimelist.net/v1/oauth2/token"
            data = {
                "client_id": self.CLIENT_ID,
                "grant_type": grant_type,
                "refresh_token": self._refresh_token,
            }

        response = self._session.post(url, data=data)
        data = response.json()

        if not isinstance(data, dict):
            raise MyAnimeListError(url, response.status_code, data)

        if not data.get("access_token") or not data.get("refresh_token"):
            raise MyAnimeListError(url, response.status_code, data)

        self._session.headers.update(
            {"Authorization": "Bearer " + data["access_token"]}
        )
        self._auth_expire_time = time_now + datetime.timedelta(
            0, int(data["expires_in"])
        )
        self._refresh_token = data["refresh_token"]




class MyAnimeListAdapter:
    def __init__(self, myanimelist: MyAnimeList, provider: "BaseProvider") -> None:
        self.mal = myanimelist
        self.provider = provider
    
    @staticmethod
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

            ratio = self._find_best_ratio(titles_mal, titles_provider)

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

            ratio = self._find_best_ratio(mal_titles, provider_titles)

            if ratio > best_ratio:
                best_ratio = ratio
                best_anime = anime

            if best_ratio == 1:
                break

        if best_ratio > minimum_similarity_ratio:
            return best_anime
