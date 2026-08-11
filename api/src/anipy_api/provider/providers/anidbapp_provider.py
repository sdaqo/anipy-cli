import re
from typing import List
from urllib.parse import urljoin

import Levenshtein
import m3u8
from anipy_api.provider import (BaseProvider, Episode, ProviderInfoResult,
                                ProviderSearchResult, ProviderStream)
from anipy_api.provider.base import LanguageTypeEnum
from anipy_api.provider.filter import (BaseFilter, FilterCapabilities, Filters,
                                       MediaType, Season, Status)
from anipy_api.provider.utils import parsenum
from anipy_api.provider import Episode
from anipy_api.error import LangTypeNotAvailableError


from bs4 import BeautifulSoup

from requests import Request

HLS_RE = re.compile(
    r"(?:file\s*:\s*|source\s*=\s*)[\"']([^\"']+\.m3u8(?:\?[^\"']*)?)[\"']",
    re.IGNORECASE,
)

class AniDBAppFilter(BaseFilter):
    def _apply_query(self, query: str):
        self._request.params["q"] = query

    def _apply_year(self, year: int): 
        self._request.params["year"] = year

    def _apply_season(self, season: Season):
        self._request.params["season"] = season.name.lower()

    def _apply_status(self, status: Status): 
        mapping = {
            Status.COMPLETED: "Finished Airing",
            Status.ONGOING: "Currently Airing",
            Status.UPCOMING: ""
        }
        self._request.params["status"] = mapping[status] 

    def _apply_media_type(self, media_type: MediaType):
        mapping = {
            MediaType.TV: "TV",
            MediaType.MOVIE: "Movie",
            MediaType.OVA: "OVA",
            MediaType.ONA: "ONA",
            MediaType.SPECIAL: "Special",
            MediaType.MUSIC: "Music"
        }
        self._request.params["type"] = mapping[media_type] 

class AniDBAppProvider(BaseProvider):
    NAME: str = "anidbapp"
    BASE_URL: str = "https://anidb.app"
    FILTER_CAPS: FilterCapabilities = FilterCapabilities.ALL

    def get_search(
        self, query: str, filters: Filters = Filters()
    ) -> List[ProviderSearchResult]:
        req = Request("GET", f"{self.BASE_URL}/browse")
        req = AniDBAppFilter(req).apply(query, filters)
        res = self._request_page(req)

        current_page = BeautifulSoup(res.text, "html.parser")
        pages = current_page.find("span", attrs={"class": "text-sm text-muted"})
        if pages:
            pages = parsenum(pages.findChildren()[-1].text)
        else: 
            pages = 1

        results: list[ProviderSearchResult] = []

        for p in range(2 if pages > 1 else 1, pages + 1):
            anime = current_page.find("div", attrs={"class": "anime-grid"}).findAll(
                "a", attrs={"class": "anime-card"}
            )

            for a in anime:
                if a is None:
                    continue

                name = a.p.text
                link = a["href"]
                ident = link.split("-")[-1]
                results.append(ProviderSearchResult(
                    identifier=ident, name=name, languages={LanguageTypeEnum.UND}
                ))

            req.params["page"] = p
            res = self._request_page(req)
            current_page = BeautifulSoup(res.text, "html.parser")

        results.sort(
            key=lambda x: Levenshtein.ratio(query, x.name, processor=str.lower),
            reverse=True,
        )

        return results

    def get_info(self, identifier: str) -> ProviderInfoResult:
        req = Request(
            "GET",
            f"{self.BASE_URL}/anime/anime-{identifier}",
        )
        res = self._request_page(req)

        soup = BeautifulSoup(res.text, "html.parser")

        name = soup.find("h1", attrs={"class": "leading-tight"})
        if name:
            name = name.text
        
        image = soup.find("img", attrs={"class": "object-cover"})
        if image:
            image = image["src"]

        year = soup.find("a", attrs={"href": re.compile(r"\/browse\?season=\w+&year=\d+")})
        if year:
            year = parsenum(year.text.split()[-1])
        
        genre_container = soup.findAll("div", attrs={"class": "flex flex-wrap gap-1.5 mb-4"})

        genres = genre_container[-1].findAll("a", attrs={"href": re.compile(r"\/(genres|themes)\/.+")})
        genres = [g.text for g in genres]

        status = soup.find("a", attrs={"href": re.compile(r"\/browse\?status=.+")})
        if status:
            mapping = {
                "Finished Airing": Status.COMPLETED,
                "Currently Airing": Status.ONGOING,
            }
            status = mapping.get(status.text, None)

        synopsis = soup.find("p", attrs={"class": "text-sm text-faint leading-relaxed"})
        if synopsis:
            synopsis = synopsis.text

        synonyms = soup.find("dt", text=re.compile(r"Synonyms"))
        if synonyms:
            synonyms = [s.strip() for s in synonyms.findNextSibling().text.split(",")]

        return ProviderInfoResult(
            name = name,
            image = image,
            genres = genres,
            synopsis = synopsis,
            status = status,
            release_year = year,
            alternative_names = synonyms
        )

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List[Episode]:
        req = Request(
            "GET",
            f"{self.BASE_URL}/api/frontend/anime/{identifier}/episodes",
        )
        res = self._request_page(req).json()
        return [e["number"] for e in res["episodes"]]

    def get_video(
        self, identifier: str, episode: Episode, lang: LanguageTypeEnum
    ) -> List[ProviderStream]:
        req = Request(
            "GET",
            f"{self.BASE_URL}/api/frontend/anime/{identifier}/episodes",
        )
        res = self._request_page(req).json().get("episodes", [])
        episode_id = next(filter(lambda e: e["number"] == episode, res))["id"]

        req = Request(
            "GET",
            f"{self.BASE_URL}/api/frontend/episode/{episode_id}/languages",
        )
        res = self._request_page(req).json().get("languages", [])
        if not res:
            return []
        
        lang_short = "eng" if lang == LanguageTypeEnum.DUB else "jpn"

        embed_url = list(filter(lambda l: l["code"] == lang_short, res))
        if not embed_url:
            raise LangTypeNotAvailableError(identifier, self.NAME, lang)
        else:
            embed_url = embed_url[0]["embed_url"]

        req = Request(
            "GET",
            embed_url,
        )
        res = self._request_page(req)

        streams = HLS_RE.findall(res.text)
        if not streams:
            return []

        sub_playlists = []
        
        for s in streams:
            req = Request("GET", s)
            res = self._request_page(req)

            content = m3u8.M3U8(res.text, base_uri=urljoin(res.url, "."))

            if len(content.playlists) == 0:
                sub_playlists.append(
                    ProviderStream(
                        url=s,
                        resolution=1080,
                        episode=episode,
                        language=lang,
                        container="hls",
                    )
                )

            for sub_playlist in content.playlists:
                sub_playlists.append(
                    ProviderStream(
                        url=urljoin(content.base_uri, sub_playlist.uri),
                        resolution=sub_playlist.stream_info.resolution[1],
                        episode=episode,
                        language=lang,
                        container="hls",
                    )
                )
        return sub_playlists
