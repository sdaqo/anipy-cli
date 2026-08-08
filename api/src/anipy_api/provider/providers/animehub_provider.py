import json
import time
import re
from typing import List
import urllib.parse
from urllib.parse import urljoin

import Levenshtein
import m3u8
from anipy_api.provider import (BaseProvider, Episode, ProviderInfoResult,
                                ProviderSearchResult, ProviderStream)
from anipy_api.provider.base import LanguageTypeEnum
from anipy_api.provider.filter import (BaseFilter, FilterCapabilities, Filters,
                                       MediaType, Season, Status)
from anipy_api.provider.utils import parsenum, request_page 
from anipy_api.provider import Episode


from bs4 import BeautifulSoup

from requests import Request


class AnimeHubFilter(BaseFilter):
    def _apply_query(self, query: str):
        if not query:
            return
        self._request.params["keyword"] = urllib.parse.quote(query)

    def _apply_year(self, year: int): 
        ...

    def _apply_season(self, season: Season):
        ...

    def _apply_status(self, status: Status): 
        ...

    def _apply_media_type(self, media_type: MediaType):
        ...

class AnimeHubProvider(BaseProvider):
    NAME: str = "animehub"
    BASE_URL: str = "https://123animehub.cc"
    FILTER_CAPS: FilterCapabilities = FilterCapabilities.NO_QUERY

    def _request_page(self, req: Request):
        res = request_page(self.session, req, False)
        
        for _ in range(5):
            if 500 <= res.status_code < 600:
                time.sleep(2)
                res = request_page(self.session, req, False)
                continue
            break

        res.raise_for_status()
        return res

    def get_search(
        self, query: str, filters: Filters = Filters()
    ) -> List[ProviderSearchResult]:
        req = Request("GET", f"{self.BASE_URL}/search")
        query = query.replace(":", "")

        req = AnimeHubFilter(req).apply(query, filters)
        res = self._request_page(req)

        current_page = BeautifulSoup(res.text, "html.parser")
        pages = current_page.find("span", attrs={"class": "total"})
        if pages:
            pages = parsenum(pages.text)
        else: return []

        results: dict[str, ProviderSearchResult] = {}

        for p in range(2 if pages > 1 else 1, pages + 1):
            anime = current_page.find("div", attrs={"class": "film-list"}).findAll(
                "div", attrs={"class": "item"}
            )

            for a in anime:
                if a is None:
                    continue

                name = a.find("a", attrs={"class": "name"})
                link: str = name["href"]

                if link.endswith("-dub"):
                    link = link[:-4]

                name = name.text

                if name.endswith(" (Dub)"):
                    name = name[:-6]

                if name.endswith(" Dub"):
                    name = name[:-4]

                lang = a.find("span", attrs={"class": re.compile(r"sub|dub")}).text
                if lang == "DUB":
                    lang = LanguageTypeEnum.DUB
                else:
                    lang = LanguageTypeEnum.SUB

                if link in results.keys():
                    results[link].languages.add(lang)
                else:
                    results[link] = ProviderSearchResult(
                        identifier=link, name=name, languages={lang}
                    )

            req.params["page"] = p
            res = self._request_page(req)
            current_page = BeautifulSoup(res.text, "html.parser")

        result_list = list(results.values())
        result_list.sort(
            key=lambda x: Levenshtein.ratio(query, x.name, processor=str.lower),
            reverse=True,
        )

        return result_list

    def get_info(self, identifier: str) -> ProviderInfoResult:
        req = Request(
            "GET",
            f"{self.BASE_URL}{identifier}",
        )
        res = self._request_page(req)

        soup = BeautifulSoup(res.text, "html.parser")

        name = soup.find("h2", attrs={"class": "title"})
        if name:
            name = name.text
            if name.endswith(" (Dub)"):
                name = name[:-6]

            if name.endswith(" Dub"):
                name = name[:-4]
        
        slug = identifier.split("/")[-1]
        image = f"{self.BASE_URL}/imgs/poster/{slug}"

        
        info_row = soup.find("div", attrs={"class": "anxmnx"})

        year = info_row.find("a", attrs={"href": re.compile(r"\/release\/\d+")})
        if year:
            year = parsenum(year.text)

        genres = info_row.findAll("a", attrs={"href": re.compile(r"\/genere\/.+")})
        genres = [g.text for g in genres]

        status = info_row.find("a", attrs={"href": re.compile(r"\/status\/.+")})
        if status:
            status = status.text

        synopsis = soup.find("div", attrs={"class": "desc"})
        if synopsis:
            synopsis = synopsis.text

        return ProviderInfoResult(
            name = name,
            image = image,
            genres = genres,
            synopsis = synopsis,
            status = status,
            release_year = year
        )

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List[Episode]:
        if lang == LanguageTypeEnum.DUB:
            identifier = identifier + "-dub"

        anime_url = f"{self.BASE_URL}{identifier}"
        slug = identifier.split("/")[-1]
        req = Request(
            "GET",
            f"{self.BASE_URL}/ajax/film/sv?id={slug}",
            headers={"Referer": anime_url},
        )
        res = self._request_page(req)

        soup = BeautifulSoup(res.json()["html"], "html.parser")
        ep_elements = soup.find("ul", attrs={"class": "episodes"}).findAll("li")

        return [parsenum(el.a["data-id"].split("/")[-1]) for el in ep_elements]

    def get_video(
        self, identifier: str, episode: Episode, lang: LanguageTypeEnum
    ) -> List[ProviderStream]:
        if lang == LanguageTypeEnum.DUB:
            identifier = identifier + "-dub"

        anime_url = f"{self.BASE_URL}{identifier}"
        slug = identifier.split("/")[-1]

        server = 0
        req = Request(
            "GET", f"{self.BASE_URL}/ajax/episode/info?epr={slug}/{episode}/{server}"
        )
        res = self._request_page(req).json()
        target = res["target"]
        target_base = target.split("/")[0] + "//" + target.split("/")[2]

        req = Request("GET", target, headers={"Referer": anime_url})
        res = self._request_page(req)
        zrpart2 = re.findall(r"var\s+zrpart2\s*=\s*['\"]([^'\"]+)['\"]", res.text)[0]

        req = Request(
            "GET", f"{target_base}/hs/{urllib.parse.quote(zrpart2, safe='')}?pl_usn=1"
        )
        res = self._request_page(req)

        soup = BeautifulSoup(res.text, "html.parser")
        sources = json.loads(soup.find("div", attrs={"id": "sources"}).text)["sources"]

        req = Request("GET", sources, headers={"Referer": target_base})
        res = self._request_page(req)
        content = m3u8.M3U8(res.text, base_uri=urljoin(res.url, "."))

        streams = []
        if len(content.playlists) == 0:
            streams.append(
                ProviderStream(
                    url=sources,
                    resolution=1080,
                    episode=episode,
                    language=lang,
                    referrer=target_base + "/",
                    container="hls",
                )
            )

        for sub_playlist in content.playlists:
            streams.append(
                ProviderStream(
                    url=urljoin(content.base_uri, sub_playlist.uri),
                    resolution=sub_playlist.stream_info.resolution[1],
                    episode=episode,
                    language=lang,
                    referrer=target_base + "/",
                    container="hls",
                )
            )

        return streams
