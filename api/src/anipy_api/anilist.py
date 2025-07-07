import datetime
import json
import base64
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set

import Levenshtein
from dataclasses_json import DataClassJsonMixin, config
from requests import Request, Session

from anipy_api.anime import Anime
from anipy_api.error import AniListError
from anipy_api.provider import (
    FilterCapabilities,
    Filters,
    MediaType,
    ProviderSearchResult,
    Season,
)

if TYPE_CHECKING:
    from anipy_api.provider import BaseProvider


class AniListMyListStatusEnum(Enum):
    """A enum of possible list states.

    Attributes:
        WATCHING:
        COMPLETED:
        ON_HOLD:
        DROPPED:
        PLAN_TO_WATCH:
        REPEATING:
    """

    WATCHING = "CURRENT"
    COMPLETED = "COMPLETED"
    ON_HOLD = "PAUSED"
    DROPPED = "DROPPED"
    PLAN_TO_WATCH = "PLANNING"
    REPEATING = "REPEATING"


class AniListMediaTypeEnum(Enum):
    """A enum of possible media types.

    Attributes:
        TV:
        TV_SHORT:
        MOVIE:
        SPECIAL:
        OVA:
        ONA:
        MUSIC:
    """

    TV = "TV"
    TV_SHORT = "TV_SHORT"
    MOVIE = "MOVIE"
    SPECIAL = "SPECIAL"
    OVA = "OVA"
    ONA = "ONA"
    MUSIC = "MUSIC"


class AniListSeasonEnum(Enum):
    """A enum of possible seasons.

    Attributes:
        WINTER:
        SPRING:
        SUMMER:
        FALL:
    """

    WINTER = "WINTER"
    SPRING = "SPRING"
    SUMMER = "SUMMER"
    # Why the hell is fall only 4 charachters long :'(
    FALL = "FALL"


@dataclass
class Picture(DataClassJsonMixin):
    large: Optional[str] = None
    medium: Optional[str] = None


@dataclass
class AniListUser(DataClassJsonMixin):
    """A json-serializable class that holds user data.

    Attributes:
        id: Users's id
        name: Users's name
        picture: Users's profile picture
    """

    id: int
    name: str
    picture: Optional[Picture] = None

def notes_to_tags(notes: Optional[str]) -> List[str]:
    if not notes:
        return []
    return [tag.strip() for tag in notes.split(",") if tag.strip()]

@dataclass
class AniListMyListStatus(DataClassJsonMixin):
    """A json-serializable class that holds a user's list status. It
    accompanies [AniListAnime][anipy_api.mal.AniListAnime].

    Attributes:
        entry_id: The unique ID of the user's list entry. Used to identify
            this anime entry in the user's AniList media list.
        num_episodes_watched: Watched episodes, this number may exceed
            that of the `num_episodes` in [AniListAnime][anipy_api.anilist.AniListAnime]
            as it can be abitrarily large.
        tags: List of tags associated with the anime
        status: Current status of the anime
        score: The user's score of the anime
    """

    entry_id: int
    notes: Optional[str]
    num_episodes_watched: int
    status: AniListMyListStatusEnum
    score: int
    tags: List[str] = field(default_factory=list, metadata=config(decoder=notes_to_tags))


@dataclass
class AniListAlternativeTitles(DataClassJsonMixin):
    """A json-serializable class that holds alternative anime titles.

    Attributes:
        en: The (offical) english variant of the name
        ja: The (offical) japanese variant of the name
        synonyms: Other synonymous names
    """

    english: Optional[str] = None
    native: Optional[str] = None
    romaji: Optional[str] = None
    # synonyms: Optional[List[str]] = None


@dataclass
class AniListStartSeason(DataClassJsonMixin):
    """A json-serializable class that holds a season/year combination
    indicating the time this anime was aired in.

    Attributes:
        season: Season of airing
        year: Year of airing
    """

    year: int
    season: AniListSeasonEnum

    def __repr__(self) -> str:
        return f"{self.season.value.capitalize()} {self.year}"


@dataclass
class Title(DataClassJsonMixin):
    user_preferred: str


@dataclass
class AniListAnime(DataClassJsonMixin):
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
    title: Title
    media_type: AniListMediaTypeEnum
    num_episodes: Optional[int] = None
    alternative_titles: Optional[AniListAlternativeTitles] = None
    year: Optional[int]  = None
    season: Optional[AniListSeasonEnum] = None
    my_list_status: Optional[AniListMyListStatus] = None

    def __repr__(self) -> str:
        return self.title.user_preferred

    def __hash__(self) -> int:
        return hash(self.id)


@dataclass
class AniListPaging(DataClassJsonMixin):
    current_page: int
    has_next_page: bool


# @dataclass
# class AniListResourceNode(DataClassJsonMixin):
#     node: AniListAnime


@dataclass
class AniListPagingResource(DataClassJsonMixin):
    page_info: AniListPaging
    media: List[AniListAnime]


class AniList:
    """MyAnimeList api client that implements some of the endpoints documented [here](https://myanimelist.net/apiconfig/references/api/v2).

    Attributes:
        API_BASE: The base url of the api (https://api.myanimelist.net/v2)
        CLIENT_ID: The client being used to access the api
        RESPONSE_FIELDS: Corresponds to fields of AniListAnime object
            (read [here](https://myanimelist.net/apiconfig/references/api/v2#section/Common-parameters)
            for explaination)
    """

    API_BASE = "https://graphql.anilist.co"
    CLIENT_ID = "28276"
    AUTH_URL = f"https://anilist.co/api/v2/oauth/authorize?client_id={CLIENT_ID}&response_type=token"

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
    def from_implicit_grant(
        access_token: str,
        client_id: Optional[str] = None
    ) -> "AniList":
        """Authenticate via Implicit Grant to retrieve access token
        
        Returns:
            The AniList client object
        """
        anilist = AniList(client_id)
        anilist._refresh_auth(access_token)
        return anilist

    def __init__(self, client_id: Optional[str] = None):
        """__init__ of AniList.

        Args:
            client_id: Overrides the default client id

        Info:
            Please note that that currently no complex oauth autentication scheme is
            implemented, this client uses the client id of the official MyAnimeList
            android app, this gives us the ability to login via a username/password
            combination. If you pass your own client id you will not be able to use
            the [from_implicit_grant][anipy_api.anilist.AniList.from_implicit_grant] function.
        """
        if client_id:
            self.CLIENT_ID = client_id
            self.AUTH_URL = f"https://anilist.co/api/v2/oauth/authorize?client_id={self.CLIENT_ID}&response_type=token"

        self._access_token = None
        self._auth_expire_time = datetime.datetime.min
        self._session = Session()
        self._session.headers.update(
            {
                "Content-Type": "application/json", 
                "Accept": "application/json",
            }
        )

    def get_search(self, search: str, limit: int = 20, pages: int = 1) -> List[AniListAnime]:
        """Search AniList.

        Args:
            search: Search query
            limit: The amount of results per page
            pages: The amount of pages to return,
                note the total number of results is limit times pages

        Returns:
            A list of search results
        """
        query = """
        query ($search: String!, $page: Int, $perPage: Int) {
          Page (page: $page, perPage: $perPage){
          page_info: pageInfo {
              currentPage
              hasNextPage
          }
          media (search: $search, type: ANIME) {
          id
          media_type: format
          num_episodes: episodes
          title {
            user_preferred: userPreferred
          }
          alternative_titles: title {
            english
            native
            romaji
          }
          year: seasonYear
          season
          my_list_status: mediaListEntry {
                entry_id: id
                notes
                num_episodes_watched: progress
                status
                score
              }
            }
          }
        }
        """

        anime_list = []
        next_page = True

        for page in range(pages):
            if next_page:
                variables = { "search": search, "page": page+1, "perPage": limit }
                request = Request("POST", self.API_BASE, json={ 'query': query, 'variables': variables })
                response = AniListPagingResource.from_dict(self._make_request(request)["data"]["Page"])
                anime_list.extend(response.media)

                next_page = response.page_info.has_next_page

        return anime_list

       

    def get_anime(self, anime_id: int) -> AniListAnime:
        """Get a MyAnimeList anime by its id.

        Args:
            anime_id: The id of the anime

        Returns:
            The anime that corresponds to the id
        """
        query = """
        query ($id: Int) {
          Media (id: $id) {
            id
            media_type: format
            num_episodes: episodes
            title {
              user_preferred: userPreferred
            }
            alternative_titles: title {
              english
              native
              romaji
            }
            year: seasonYear
            season
            my_list_status: mediaListEntry {
              entry_id: id
              notes
              num_episodes_watched: progress
              status
              score
            }
          }
        }
        """
        variables = { "id": anime_id }
        request = Request("POST", self.API_BASE, json={ 'query': query, 'variables': variables })
        return AniListAnime.from_dict(self._make_request(request)["data"]["Media"])

    def get_user(self) -> AniListUser:
        """Get information about the currently authenticated user.

        Returns:
            A object with user information
        """
        query="""
        query {
          Viewer {
            id
            name
            picture: avatar {
                  large
                  medium
            }
          }
        }
        """
        request = Request(
                "POST", self.API_BASE, json={ 'query': query }
        )
        return AniListUser.from_dict(self._make_request(request)["data"]["Viewer"])

    def get_anime_list(
        self, status_filter: Optional[AniListMyListStatusEnum] = None
    ) -> List[AniListAnime]:
        """Get the anime list of the currently authenticated user.

        Args:
            status_filter: A filter that determines which list status is retrieved

        Returns:
            List of anime in the anime list
        """
        query = """
        query ($type: MediaType!, $userId: Int!) {
          MediaListCollection(type: $type, userId: $userId) {
            lists {
              entries {
                id
                media {
                  id
                  media_type: format
                  num_episodes: episodes
                  title {
                      user_preferred: userPreferred
                  }
                  alternative_titles: title {
                      english
                      native
                      romaji
                  }
                  year: seasonYear
                    season
                    my_list_status: mediaListEntry {
                      entry_id: id
                      notes
                      num_episodes_watched: progress
                      status
                      score
                    }
                }
              }
            }
          }
        }
        """
        user_id = self.get_user().id
        variables = { "type": "ANIME", "userId": user_id }
        request = Request("POST", self.API_BASE, json={ 'query': query, 'variables': variables })
       
        anime_list = []
        for group in self._make_request(request)["data"]["MediaListCollection"]["lists"]:
            for entry in group["entries"]:
                anime = AniListAnime.from_dict(entry["media"])
                user_status = anime.my_list_status.status if anime.my_list_status else None
                if status_filter is None or user_status == status_filter:
                    anime_list.append(anime)

        return anime_list

    def update_anime_list(
        self,
        anime_id: int,
        status: Optional[AniListMyListStatusEnum] = None,
        watched_episodes: Optional[int] = None,
        tags: Optional[List[str]] = None,
    ) -> AniListMyListStatus:
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
        query = """
        mutation ($listEntryId: Int, $status: MediaListStatus, $episodes: Int, $notes: String) {
          SaveMediaListEntry(id: $listEntryId, status: $status, progress: $episodes, notes: $notes) {
            entry_id: id
            notes
            num_episodes_watched: progress
            status
            score
          }
        }
        """
        my_list_status = self.get_anime(anime_id).my_list_status
        if not my_list_status:
            raise ValueError(f"No existing list entry found for anime ID {anime_id}.")
        list_entry_id = my_list_status.entry_id
        variables = {
            k: v
            for k, v in {
                "listEntryId": list_entry_id,
                "status": status.value if status else None,
                "num_watched_episodes": watched_episodes,
                "tags": ",".join(tags) if tags is not None else None,
            }.items()
            if v is not None
        }
        request = Request("POST", self.API_BASE, json={ 'query': query, 'variables': variables })

        return AniListMyListStatus.from_dict(self._make_request(request)["data"]["SaveMediaListEntry"])

    def remove_from_anime_list(self, anime_id: int):
        """Remove an anime from the currently authenticated user's anime list.

        Args:
            anime_id: Id of the anime to be removed
        """
        query = """
        mutation ($listEntryId: Int!) {
          DeleteMediaListEntry(id: $listEntryId) {
            deleted
          }
        }
        """
        my_list_status = self.get_anime(anime_id).my_list_status
        if my_list_status:
            list_entry_id = my_list_status.entry_id
            variables = { "listEntryId": list_entry_id }
            request = Request("POST", self.API_BASE, json={ 'query': query, 'variables': variables})
            self._make_request(request)


    def _make_request(self, request: Request) -> Dict[str, Any]:
        prepped = request.prepare()
        prepped.headers.update(self._session.headers)  # type: ignore

        response = self._session.send(prepped)

        if response.ok:
            return response.json()

        # if response.status_code == 400:
        #     self._refresh_auth()
        #     return self._make_request(request)

        raise AniListError(response.url, response.status_code, response.json())

    def _jwt_decode(self, token: str) -> Dict[str,Any]:
        jwt_encoded = token.split('.')
        for index, i in enumerate(jwt_encoded):
            missing_padding = 4 - len(i) % 4
            if missing_padding != 4:
                jwt_encoded[index] += '='*missing_padding
        
        expire_time = datetime.datetime.fromtimestamp(int(json.loads(base64.urlsafe_b64decode(jwt_encoded[1]))["exp"]))
        return { "token": token, "expire_time": expire_time }

    def _refresh_auth(self, access_token: str):
        time_now = datetime.datetime.now()
        if self._auth_expire_time > time_now:
            return True
        
        jwt_decoded = self._jwt_decode(access_token)
        self._access_token = jwt_decoded["token"]
        self._session.headers.update(
            { "Authorization": "Bearer " + self._access_token }
        )
        self._auth_expire_time = jwt_decoded["expire_time"]


class AniListAdapter:
    """A adapter class that can adapt MyAnimeList anime to Provider anime.

    Attributes:
        anilist: The AniList object
        provider: The provider object
    """

    def __init__(self, myanimelist: AniList, provider: "BaseProvider") -> None:
        """__init__ of MyAnimeListAdapter.

        Args:
            anilist: The AniList object to use
            provider: The provider object to use
        """
        self.anilist: AniList = myanimelist
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
    ) -> Optional[AniListAnime]:
        """Adapt an anime from provider [Anime][anipy_api.anime.Anime] to a [AniListAnime][anipy_api.anilist.AniListAnime].
        This uses [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance) to calculate the similarity of names.

        Args:
            anime: The anime to adapt from
            minimum_similarity_ratio: The minimum accepted similarity ratio. This should be a number from 0-1,
                1 meaning the names are identical 0 meaning there are no identical charachters whatsoever.
                If it is not met the function will return None.
            use_alternative_names: Use alternative names for matching, this may yield a higher chance of finding
                a match but takes more time.

        Returns:
            A AniListAnime object if adapting was successfull
        """
        results = self.anilist.get_search(anime.name)

        best_anime = None
        best_ratio = 0
        for i in results:
            titles_mal = {i.title.user_preferred}
            titles_provider = {anime.name}

            if use_alternative_names:
                if i.alternative_titles is not None:
                    titles_mal |= {
                        t
                        for t in [i.alternative_titles.native, i.alternative_titles.english]
                        if t is not None
                    }
                    titles_mal |= (
                        set(i.alternative_titles.romaji)
                        if i.alternative_titles.romaji is not None
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

    def from_anilist(
        self,
        anilist_anime: AniListAnime,
        minimum_similarity_ratio: float = 0.8,
        use_filters: bool = True,
        use_alternative_names: bool = True,
    ) -> Optional[Anime]:
        """Adapt an anime from a [AniListAnime][anipy_api.anilist.AniListAnime] to a provider [Anime][anipy_api.anime.Anime].
        This uses [Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance) to calculate the similarity of names.

        Args:
            anilist_anime: The anilist anime to adapt from
            minimum_similarity_ratio: The minimum accepted similarity ratio. This should be a number from 0-1,
                1 meaning the names are identical 0 meaning there are no identical charachters whatsoever.
                If it is not met the function will return None.
            use_filters: Use filters for the provider to cut down on possible wrong results, do note that this will take more time.
            use_alternative_names: Use alternative names for matching, this may yield a higher chance of finding a match but takes more time.

        Returns:
            A Anime object if adapting was successfull

        """
        anilist_titles = {anilist_anime.title.user_preferred}
        if use_alternative_names and anilist_anime.alternative_titles is not None:
            anilist_titles |= {
                t
                for t in [
                    anilist_anime.alternative_titles.native,
                    anilist_anime.alternative_titles.english,
                    anilist_anime.alternative_titles.romaji
                ]
                if t is not None
            }

        provider_filters = Filters()
        if (
            self.provider.FILTER_CAPS & FilterCapabilities.YEAR
            and anilist_anime.season is not None
        ):
            provider_filters.year = anilist_anime.year

        if (
            self.provider.FILTER_CAPS & FilterCapabilities.SEASON
            and anilist_anime.season is not None
        ):
            provider_filters.season = Season[
                anilist_anime.season.value.upper()
            ]

        if self.provider.FILTER_CAPS & FilterCapabilities.MEDIA_TYPE:
            if anilist_anime.media_type == AniListMediaTypeEnum.TV_SHORT:
                m_type = AniListMediaTypeEnum.TV
            else:
                m_type = anilist_anime.media_type

            provider_filters.media_type = MediaType[m_type.value.upper()]

        results: Set[ProviderSearchResult] = set()
        for title in anilist_titles:
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
                anime_info = anime.get_info()
                if anime_info.release_year == anilist_anime.year:
                    provider_titles |= set(anime_info.alternative_names or [])
                else:
                    continue

            ratio = self._find_best_ratio(anilist_titles, provider_titles)

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
