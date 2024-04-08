import datetime
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from dataclasses_json import DataClassJsonMixin, Undefined
from requests import Request, Session

from anipy_cli.error import MyAnimeListError
from anipy_cli.version import __appname__, __version__


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
        status: Optional[MALMyListStatusEnum],
        watched_episodes: Optional[int],
        tags: Optional[List[str]],
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
