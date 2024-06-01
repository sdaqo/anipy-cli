import datetime
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

import Levenshtein
from dataclasses_json import DataClassJsonMixin
from requests import Request, Session

from anipy_api.anime import Anime
from anipy_api.error import MyAnimeListError
from anipy_api.provider import (
    FilterCapabilities,
    Filters,
    MediaType,
    ProviderSearchResult,
    Season,
)

if TYPE_CHECKING:
    from anipy_api.provider import BaseProvider


class MALMyListStatusEnum(Enum):
    """A enum of possible list states.

    Attributes:
        WATCHING:
        COMPLETED:
        ON_HOLD:
        DROPPED:
        PLAN_TO_WATCH:
    """

    WATCHING = "watching"
    COMPLETED = "completed"
    ON_HOLD = "on_hold"
    DROPPED = "dropped"
    PLAN_TO_WATCH = "plan_to_watch"


class MALMediaTypeEnum(Enum):
    """A enum of possible media types.

    Attributes:
        TV:
        MOVIE:
        OVA:
        ONA:
        SPECIAL:
        TV_SPECIAL:
        MUSIC:
        CM:
        UNKNOWN:
    """

    TV = "tv"
    MOVIE = "movie"
    OVA = "ova"
    ONA = "ona"
    SPECIAL = "special"
    TV_SPECIAL = "tv_special"
    MUSIC = "music"
    CM = "cm"
    UNKNOWN = "unknown"


class MALSeasonEnum(Enum):
    """A enum of possible seasons.

    Attributes:
        WINTER:
        SPRING:
        SUMMER:
        FALL:
    """

    WINTER = "winter"
    SPRING = "spring"
    SUMMER = "summer"
    # Why the hell is fall only 4 charachters long :'(
    FALL = "fall"


@dataclass
class MALUser(DataClassJsonMixin):
    """A json-serializable class that holds user data.

    Attributes:
        id: Users's id
        name: Users's name
        picture: Users's profile picture
    """

    id: int
    name: str
    picture: Optional[str] = None


@dataclass
class MALMyListStatus(DataClassJsonMixin):
    """A json-serializable class that holds a user's list status. It
    accompanies [MALAnime][anipy_api.mal.MALAnime].

    Attributes:
        num_episodes_watched: Watched episodes, this number may exceed
            that of the `num_episodes` in [MALAnime][anipy_api.mal.MALAnime]
            as it can be abitrarily large.
        tags: List of tags associated with the anime
        status: Current status of the anime
        score: The user's score of the anime
    """

    num_episodes_watched: int
    tags: List[str]
    status: MALMyListStatusEnum
    score: int


@dataclass
class MALAlternativeTitles(DataClassJsonMixin):
    """A json-serializable class that holds alternative anime titles.

    Attributes:
        en: The (offical) english variant of the name
        ja: The (offical) japanese variant of the name
        synonyms: Other synonymous names
    """

    en: Optional[str] = None
    ja: Optional[str] = None
    synonyms: Optional[List[str]] = None


@dataclass
class MALStartSeason(DataClassJsonMixin):
    """A json-serializable class that holds a season/year combination
    indicating the time this anime was aired in.

    Attributes:
        season: Season of airing
        year: Year of airing
    """

    season: MALSeasonEnum
    year: int

    def __repr__(self) -> str:
        return f"{self.season.value.capitalize()} {self.year}"


@dataclass
class MALAnime(DataClassJsonMixin):
    """A json-serializable class that holds information about an anime and the
    user's list status if the anime is in their list.

    Attributes:
        id: Id of the anime
        title: Title of the anime
        media_type: Media type of the anime
        num_episodes: Number of episodes the anime has, if unknown it is 0
        alternative_titles: Alternative titles for an anime
        start_season: Season/Year the anime started in
        my_list_status: If the anime is in the user's list,
            this holds the information of the list status
    """

    id: int
    title: str
    media_type: MALMediaTypeEnum
    num_episodes: int
    alternative_titles: Optional[MALAlternativeTitles] = None
    start_season: Optional[MALStartSeason] = None
    my_list_status: Optional[MALMyListStatus] = None

    def __repr__(self) -> str:
        return self.title

    def __hash__(self) -> int:
        return hash(self.id)


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
    """MyAnimeList api client that implements some of the endpoints documented [here](https://myanimelist.net/apiconfig/references/api/v2).

    Attributes:
        API_BASE: The base url of the api (https://api.myanimelist.net/v2)
        CLIENT_ID: The client being used to access the api
        RESPONSE_FIELDS: Corresponds to fields of MALAnime object
            (read [here](https://myanimelist.net/apiconfig/references/api/v2#section/Common-parameters)
            for explaination)
    """

    API_BASE = "https://api.myanimelist.net/v2"
    CLIENT_ID = "6114d00ca681b7701d1e15fe11a4987e"

    # Corresponds to fields of MALAnime object
    RESPONSE_FIELDS = [
        "id",
        "title",
        "alternative_titles",
        "start_season",
        "media_type",
        "num_episodes",
        "my_list_status{tags,num_episodes_watched,score,status}",
    ]

    @staticmethod
    def from_password_grant(
        user: str, password: str, client_id: Optional[str] = None
    ) -> "MyAnimeList":
        """Authenticate via a username/password combination.

        Args:
            user: MyAnimeList username
            password: MyAnimeList password
            client_id: Overrides the default client id

        Returns:
            The MyAnimeList client object
        """
        mal = MyAnimeList(client_id)
        mal._refresh_auth(user, password)
        return mal

    @staticmethod
    def from_rt_grant(
        refresh_token: str, client_id: Optional[str] = None
    ) -> "MyAnimeList":
        """Authenticate via a refresh token. The refresh token will be saved in
        `MyAnimeList._refresh_token` and used to periodically refresh the
        access token, the refresh token may change if the current one expires.

        Args:
            refresh_token: The refresh token
            client_id: Overrides the default client id

        Returns:
            The MyAnimeList client object
        """
        mal = MyAnimeList(client_id)
        mal._refresh_token = refresh_token
        mal._refresh_auth()
        return mal

    def __init__(self, client_id: Optional[str] = None):
        """__init__ of MyAnimeList.

        Args:
            client_id: Overrides the default client id

        Info:
            Please note that that currently no complex oauth autentication scheme is
            implemented, this client uses the client id of the official MyAnimeList
            android app, this gives us the ability to login via a username/password
            combination. If you pass your own client id you will not be able to use
            the [from_password_grant][anipy_api.mal.MyAnimeList.from_password_grant] function.
        """
        if client_id:
            self.CLIENT_ID = client_id

        self._refresh_token = None
        self._auth_expire_time = datetime.datetime.min

        self._session = Session()
        self._session.headers.update(
            {
                "X-MAL-Client-ID": self.CLIENT_ID,
            }
        )

    def get_search(self, query: str, limit: int = 20, pages: int = 1) -> List[MALAnime]:
        """Search MyAnimeList.

        Args:
            query: Search query
            limit: The amount of results per page
            pages: The amount of pages to return,
                note the total number of results is limit times pages

        Returns:
            A list of search results
        """
        return self._get_resource("anime", {"q": query}, limit, pages)

    def get_anime(self, anime_id: int) -> MALAnime:
        """Get a MyAnimeList anime by its id.

        Args:
            anime_id: The id of the anime

        Returns:
            The anime that corresponds to the id
        """
        request = Request("GET", f"{self.API_BASE}/anime/{anime_id}")
        return MALAnime.from_dict(self._make_request(request))

    def get_user(self) -> MALUser:
        """Get information about the currently authenticated user.

        Returns:
            A object with user information
        """
        request = Request(
            "GET", f"{self.API_BASE}/users/@me", params={"fields": "id,name,picture"}
        )
        return MALUser.from_dict(self._make_request(request))

    def get_anime_list(
        self, status_filter: Optional[MALMyListStatusEnum] = None
    ) -> List[MALAnime]:
        """Get the anime list of the currently authenticated user.

        Args:
            status_filter: A filter that determines which list status is retrieved

        Returns:
            List of anime in the anime list
        """
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
        """Update a specific anime in the currently authenticated users's anime
        list. Only pass the arguments you want to update.

        Args:
            anime_id: The anime id of the anime to update
            status: Updated status of the anime
            watched_episodes: Updated watched episodes
            tags: Updated list of tags, note that this **ovewrites** the already
                existing tags, if you want to retain the old ones you have to merge
                the old ones with the new ones yourself.

        Returns:
            Object of the updated anime
        """
        data = {
            k: v
            for k, v in {
                "status": status.value if status else None,
                "num_watched_episodes": watched_episodes,
                "tags": ",".join(tags) if tags is not None else None,
            }.items()
            if v is not None
        }
        request = Request(
            "PATCH", f"{self.API_BASE}/anime/{anime_id}/my_list_status", data=data
        )

        return MALMyListStatus.schema(unknown="exclude").load(
            self._make_request(request)
        )

    def remove_from_anime_list(self, anime_id: int):
        """Remove an anime from the currently authenticated user's anime list.

        Args:
            anime_id: Id of the anime to be removed
        """
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
            response = MALPagingResource.from_dict(self._make_request(request))

            if response.paging.next:
                offset += limit
                pages -= 1
            else:
                next_page = False

            anime_list.extend([i.node for i in response.data])

            if pages == 0:
                next_page = False

        return anime_list

    def _make_request(self, request: Request) -> Dict[str, Any]:
        prepped = request.prepare()
        prepped.headers.update(self._session.headers)  # type: ignore

        response = self._session.send(prepped)

        if response.ok:
            return response.json()

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
    """A adapter class that can adapt MyAnimeList anime to Provider anime.

    Attributes:
        mal: The MyAnimeList object
        provider: The provider object
    """

    def __init__(self, myanimelist: MyAnimeList, provider: "BaseProvider") -> None:
        """__init__ of MyAnimeListAdapter.

        Args:
            myanimelist: The MyAnimeList object to use
            provider: The provider object to use
        """
        self.mal: MyAnimeList = myanimelist
        self.provider: "BaseProvider" = provider

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
        """Adapt an anime from provider [Anime][anipy_api.anime.Anime] to a [MALAnime][anipy_api.mal.MALAnime].
        This uses [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance) to calculate the similarity of names.

        Args:
            anime: The anime to adapt from
            minimum_similarity_ratio: The minimum accepted similarity ratio. This should be a number from 0-1,
                1 meaning the names are identical 0 meaning there are no identical charachters whatsoever.
                If it is not met the function will return None.
            use_alternative_names: Use alternative names for matching, this may yield a higher chance of finding
                a match but takes more time.

        Returns:
            A MALAnime object if adapting was successfull
        """
        results = self.mal.get_search(anime.name)

        best_anime = None
        best_ratio = 0
        for i in results:
            titles_mal = {i.title}
            titles_provider = {anime.name}

            if use_alternative_names:
                if i.alternative_titles is not None:
                    titles_mal |= {
                        t
                        for t in [i.alternative_titles.ja, i.alternative_titles.en]
                        if t is not None
                    }
                    titles_mal |= (
                        set(i.alternative_titles.synonyms)
                        if i.alternative_titles.synonyms is not None
                        else set()
                    )
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
        """Adapt an anime from a [MALAnime][anipy_api.mal.MALAnime] to a provider [Anime][anipy_api.anime.Anime].
        This uses [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance) to calculate the similarity of names.

        Args:
            mal_anime: The mal anime to adapt from
            minimum_similarity_ratio: The minimum accepted similarity ratio. This should be a number from 0-1,
                1 meaning the names are identical 0 meaning there are no identical charachters whatsoever.
                If it is not met the function will return None.
            use_filters: Use filters for the provider to cut down on possible wrong results, do note that this will take more time.
            use_alternative_names: Use alternative names for matching, this may yield a higher chance of finding a match but takes more time.

        Returns:
            A Anime object if adapting was successfull

        """
        mal_titles = {mal_anime.title}
        if use_alternative_names and mal_anime.alternative_titles is not None:
            mal_titles |= {
                t
                for t in [
                    mal_anime.alternative_titles.ja,
                    mal_anime.alternative_titles.en,
                ]
                if t is not None
            }
            mal_titles |= (
                set(mal_anime.alternative_titles.synonyms)
                if mal_anime.alternative_titles.synonyms is not None
                else set()
            )

        provider_filters = Filters()
        if (
            self.provider.FILTER_CAPS & FilterCapabilities.YEAR
            and mal_anime.start_season is not None
        ):
            provider_filters.year = mal_anime.start_season.year

        if (
            self.provider.FILTER_CAPS & FilterCapabilities.SEASON
            and mal_anime.start_season is not None
        ):
            provider_filters.season = Season[
                mal_anime.start_season.season.value.upper()
            ]

        if self.provider.FILTER_CAPS & FilterCapabilities.MEDIA_TYPE:
            if mal_anime.media_type not in (
                MALMediaTypeEnum.UNKNOWN,
                MALMediaTypeEnum.CM,
            ):
                if mal_anime.media_type == MALMediaTypeEnum.TV_SPECIAL:
                    m_type = MALMediaTypeEnum.SPECIAL
                else:
                    m_type = mal_anime.media_type

                provider_filters.media_type = MediaType[m_type.value.upper()]

        results: Set[ProviderSearchResult] = set()
        for title in mal_titles:
            if len(title) == 0:
                continue

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
            elif (
                best_anime is not None
                and ratio == best_ratio
                and len(anime.languages) > len(best_anime.languages)
            ):
                # prefer anime with more language options
                best_anime = anime

            if best_ratio == 1:
                break

        if best_ratio > minimum_similarity_ratio:
            return best_anime
