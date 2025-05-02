import json
from typing import TYPE_CHECKING, List
from urllib.parse import urljoin

import m3u8
import Levenshtein
from requests import Request
from requests.exceptions import HTTPError

from anipy_api.provider import (
    BaseProvider,
    ProviderInfoResult,
    ProviderSearchResult,
    ProviderStream,
    Episode,
)
from anipy_api.provider.base import ExternalSub, LanguageTypeEnum
from anipy_api.provider.filter import (
    BaseFilter,
    FilterCapabilities,
    Filters,
    MediaType,
    Season,
    Status,
)
from anipy_api.provider.utils import get_language_name, parsenum
from copy import deepcopy

if TYPE_CHECKING:
    from anipy_api.provider import Episode


SEARCH_QURY = """
    query( $search: SearchInput
           $limit: Int
           $page: Int
           $translationType: VaildTranslationTypeEnumType
           $countryOrigin: VaildCountryOriginEnumType )
    {
        shows( search: $search
                limit: $limit
                page: $page
                translationType: $translationType
                countryOrigin: $countryOrigin )
        {
            edges 
            {
                _id,
                name,
                availableEpisodes
            }
        }
    }
"""

EPISODES_QUERY = """
    query ($showId: String!) {
        show(
            _id: $showId
        ) {
            availableEpisodesDetail,
        }
    }
"""

STREAMURL_QUERY = """
    query ($showId: String!, $translationType: VaildTranslationTypeEnumType!, $episodeString: String!) {
        episode(
            showId: $showId
            translationType: $translationType
            episodeString: $episodeString
        ) {
            episodeString,
            sourceUrls
        }
    }
"""


INFO_QUERY = """
    query ($showId: String!) {
        show(
            _id: $showId
        ) {
            name,
            altNames,
            thumbnail,
            genres,
            status,
            airedStart,
            description
        }
    }
"""


class AllAnimeFilter(BaseFilter):
    def _apply_query(self, query: str):
        if not query:
            return
        self._request.params["variables"]["search"].update({"query": query})

    def _apply_year(self, year: int):
        self._request.params["variables"]["search"].update({"year": int(year)})

    def _apply_season(self, season: Season):
        season_name = season.name.capitalize()
        self._request.params["variables"]["search"].update({"season": season_name})

    def _apply_status(self, status: Status): ...

    def _apply_media_type(self, media_type: MediaType):
        mapping = {
            MediaType.TV: "TV",
            MediaType.SPECIAL: "Special",
            MediaType.MOVIE: "Movie",
            MediaType.OVA: "OVA",
            MediaType.ONA: "ONA",
        }
        self._request.params["variables"]["search"].update(
            {"types": [mapping[media_type]]}
        )


class AllAnimeProvider(BaseProvider):
    """For detailed documentation have a look
    at the [base class][anipy_api.provider.base.BaseProvider].

    Attributes:
        NAME: allanime
        BASE_URL: https://allanime.day
        FILTER_CAPS: YEAR, MEDIA_TYPE, SEASON, NO_QUERY
    """

    NAME: str = "allanime"
    BASE_URL: str = "https://allanime.day"
    FILTER_CAPS: FilterCapabilities = (
        FilterCapabilities.YEAR
        | FilterCapabilities.MEDIA_TYPE
        | FilterCapabilities.SEASON
        | FilterCapabilities.NO_QUERY
    )

    API_URL: str = BASE_URL.replace("//", "//api.") + "/api"

    def get_search(
        self, query: str, filters: "Filters" = Filters()
    ) -> List[ProviderSearchResult]:
        req = Request(
            "GET",
            self.API_URL,
            params={
                "variables": {
                    "search": {},
                    "limit": 26,
                    "page": 1,
                    "countryOrigin": "ALL",
                },
                "query": SEARCH_QURY,
            },
            headers={"Referer": "https://allmanga.to/"},
        )
        req = AllAnimeFilter(req).apply(query, filters)

        results = []
        page = 1
        while True:
            req.params["variables"]["page"] = page
            final_req = deepcopy(req)
            final_req.params["variables"] = json.dumps(final_req.params["variables"])
            res = self._request_page(final_req).json()

            provider_results = res["data"]["shows"]["edges"]
            if len(provider_results) == 0:
                break

            for a in provider_results:
                name = a["name"]
                identifier = a["_id"]
                languages = {LanguageTypeEnum.SUB}
                if a["availableEpisodes"]["dub"] > 0:
                    languages |= {LanguageTypeEnum.DUB}

                results.append(
                    ProviderSearchResult(
                        identifier=identifier, name=name, languages=languages
                    )
                )
            page += 1
        
        # The results are not sorted properly so sort by best match to query
        results.sort(
            key=lambda x: Levenshtein.ratio(query, x.name, processor=str.lower), 
            reverse=True
        )

        return results

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List[Episode]:
        req = Request(
            "GET",
            self.API_URL,
            params={
                "variables": json.dumps({"showId": identifier}),
                "query": EPISODES_QUERY,
            },
            headers={"Referer": "https://allmanga.to/"},
        )
        result = self._request_page(req).json()

        if lang == LanguageTypeEnum.DUB:
            episodes = result["data"]["show"]["availableEpisodesDetail"]["dub"]
        else:
            episodes = result["data"]["show"]["availableEpisodesDetail"]["sub"]

        return sorted([parsenum(e) for e in episodes])

    def get_info(self, identifier: str) -> "ProviderInfoResult":
        req = Request(
            "GET",
            self.API_URL,
            params={
                "variables": json.dumps({"showId": identifier}),
                "query": INFO_QUERY,
            },
            headers={"Referer": "https://allmanga.to/"},
        )
        result = self._request_page(req).json()
        data = result["data"]["show"]

        status_map = {"Releasing": Status.ONGOING, "Finished": Status.COMPLETED}

        return ProviderInfoResult(
            name=data.get("name", None),
            image=data.get("thumbnail", None),
            genres=data.get("genres", None),
            status=status_map.get(data["status"], None),
            synopsis=data.get("description", None),
            release_year=data.get("airedStart", {}).get("year", None),
            alternative_names=data.get("altNames", None),
        )

    def get_video(
        self, identifier: str, episode: Episode, lang: LanguageTypeEnum
    ) -> List[ProviderStream]:
        tt = "dub" if lang == LanguageTypeEnum.DUB else "sub"
        req = Request(
            "GET",
            self.API_URL,
            params={
                "variables": json.dumps(
                    {
                        "showId": identifier,
                        "translationType": tt,
                        "episodeString": str(episode),
                    }
                ),
                "query": STREAMURL_QUERY,
            },
            headers={"Referer": "https://allmanga.to/"},
        )
        result = self._request_page(req).json()

        providers = ["Yt-mp4", "Luf-Mp4", "S-Mp4", "Default"]

        streams = []

        for provider in result["data"]["episode"]["sourceUrls"]:
            if provider["sourceName"] not in providers:
                continue

            decrypted_path = self._decrypt(
                provider["sourceUrl"].replace("--", "")
            ).replace("clock", "clock.json")

            if "tools.fast4speed.rsvp" in decrypted_path:
                streams.append(
                    ProviderStream(
                        url=decrypted_path,
                        resolution=1080,
                        episode=episode,
                        language=lang,
                        referrer=self.BASE_URL,
                    )
                )
                continue

            req = Request(
                "GET",
                f"{self.BASE_URL}{decrypted_path}",
                headers={"Referer": "https://allmanga.to/"},
            )
            try:
                for attempts in range(3):
                    raw_result = self._request_page(req)
                    if raw_result.text != "":
                        break
                else:
                    raise ConnectionError("Server responded with empty data.")

                result = raw_result.json()
            except HTTPError:
                continue

            for links in result["links"]:
                link = links["link"]
                if "repackager.wixmp.com" in link:
                    link = link.split(".urlset")[0]
                    link = link.replace("repackager.wixmp.com/", "")
                    link = link.split(",")
                    part_one = link[0]
                    part_two = link[-1]
                    for qual in link[1:-1]:
                        streams.append(
                            ProviderStream(
                                url=part_one + qual + part_two,
                                resolution=int(qual.replace("p", "")),
                                episode=episode,
                                language=lang,
                                referrer=self.BASE_URL,
                            )
                        )
                    continue

                subs_provider = links.get("subtitles", [])
                subs = {}

                for sub in subs_provider:
                    subs[sub["label"]] = ExternalSub(
                        url=sub["src"],
                        shortcode=sub["lang"],
                        codec="vtt",
                        lang=get_language_name(sub["lang"]) or sub["label"],
                    )

                referer = links.get("headers", {}).get("Referer", self.BASE_URL)
                req = Request("GET", link, headers={"Referer": referer})
                try:
                    result = self._request_page(req)
                except HTTPError:
                    continue

                base_uri = urljoin(link, ".")

                content = m3u8.M3U8(result.text, base_uri=base_uri)
                playlists_resolution = []

                if len(content.playlists) == 0:
                    playlists_resolution.append((link, 1080))
                else:
                    for sub_playlist in content.playlists:
                        playlists_resolution.append(
                            (
                                urljoin(base_uri, sub_playlist.uri),
                                sub_playlist.stream_info.resolution[1],
                            )
                        )

                for plst in playlists_resolution:
                    streams.append(
                        ProviderStream(
                            url=plst[0],
                            resolution=plst[1],
                            episode=episode,
                            language=lang,
                            subtitle=subs if subs else None,
                            referrer=referer,
                        )
                    )
        return streams

    @staticmethod
    def _decrypt(provider_id) -> str:
        decrypted = ""
        for hex_value in [
            provider_id[i : i + 2] for i in range(0, len(provider_id), 2)
        ]:
            dec = int(hex_value, 16)
            xor = dec ^ 56
            oct_value = oct(xor)[2:].zfill(3)
            decrypted += chr(int(oct_value, 8))
        return decrypted
