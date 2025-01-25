import re
from typing import TYPE_CHECKING, List
from urllib.parse import urljoin

from anipy_api.provider.utils import parsenum, safe_attr
import m3u8
from bs4 import BeautifulSoup
from requests import Request

from anipy_api.error import BeautifulSoupLocationError, LangTypeNotAvailableError
from anipy_api.provider import (
    BaseProvider,
    LanguageTypeEnum,
    ProviderInfoResult,
    ProviderSearchResult,
    ProviderStream,
)
from anipy_api.provider.filter import (
    BaseFilter,
    FilterCapabilities,
    Filters,
    MediaType,
    Season,
    Status,
)

if TYPE_CHECKING:
    from anipy_api.provider import Episode


class AnivibeFilter(BaseFilter):
    def _apply_query(self, query: str):
        self._request.params.update({"keyword": query})

    def _apply_year(self, year: int):
        self._request.params.update({"year[]": [year]})

    def _apply_season(self, season: Season):
        mapping = {
            Season.WINTER: 1,
            Season.SPRING: 2,
            Season.SUMMER: 3,
            Season.FALL: 4,
        }
        self._request.params.update({"season[]": [mapping[season]]})

    def _apply_status(self, status: Status):
        mapping = {v: k.capitalize() for k, v in Status._member_map_.items()}
        self._request.params.update({"status[]": [mapping[status]]})

    def _apply_media_type(self, media_type: MediaType):
        mapping = {
            MediaType.MOVIE: [1],
            MediaType.TV: [2],
            MediaType.OVA: [3],
            MediaType.SPECIAL: [4, 7],
            MediaType.ONA: [5],
            MediaType.MUSIC: [6],
        }
        self._request.params.update({"type[]": mapping[media_type]})


class AnivibeProvider(BaseProvider):
    """For detailed documentation have a look
    at the [base class][anipy_api.provider.base.BaseProvider].

    Attributes:
        NAME: anivibe
        BASE_URL: https://anivibe.net
        FILTER_CAPS: YEAR, SEASON, STATUS, MEDIA_TYPE, NO_QUERY
    """

    NAME: str = "anivibe"
    BASE_URL: str = "https://anivibe.net"
    FILTER_CAPS: FilterCapabilities = (
        FilterCapabilities.YEAR
        | FilterCapabilities.SEASON
        | FilterCapabilities.STATUS
        | FilterCapabilities.MEDIA_TYPE
        | FilterCapabilities.NO_QUERY
    )

    def get_search(
        self, query: str, filters: "Filters" = Filters()
    ) -> List[ProviderSearchResult]:
        search_url = self.BASE_URL + "/search.html"
        req = Request("GET", search_url)
        req = AnivibeFilter(req).apply(query, filters)

        results = []
        has_next = True
        page = 0
        while has_next:
            req.params["page"] = page + 1
            res = self._request_page(req)
            soup = BeautifulSoup(res.text, "html.parser")
            has_next = bool(soup.find("li", attrs={"class": "page-item next"}))
            anime = soup.find_all("article")
            for a in anime:
                uri = a.div.a["href"]
                identifier = uri.split("/")[-1]
                if identifier is None:
                    continue

                name = a.find("span", attrs={"class": "d-title"}).get_text()

                languages = set()
                has_sub = a.find("span", attrs={"class": "sb sub"})
                if has_sub is not None:
                    languages.add(LanguageTypeEnum.SUB)

                has_dub = a.find("span", attrs={"class": "sb dub"})
                if has_dub is not None:
                    languages.add(LanguageTypeEnum.DUB)

                if len(languages) == 0:
                    languages.add(LanguageTypeEnum.SUB)

                results.append(
                    ProviderSearchResult(
                        identifier=identifier, name=name, languages=languages
                    )
                )

            page += 1
        return results

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List["Episode"]:
        req = Request("GET", f"{self.BASE_URL}/series/{identifier}")
        result = self._request_page(req)
        soup = BeautifulSoup(result.text, "html.parser")
        ep_elements = soup.find_all("li", attrs={"data-index": re.compile(r"\d")})
        ep_list = []
        for e in ep_elements:
            episode = safe_attr(e.find("div", class_="epl-num"), "text")
            if episode is None:
                raise BeautifulSoupLocationError("episode", result.url)
            ep_list.append(parsenum(episode))
        ep_list.reverse()

        return ep_list

    def get_info(self, identifier: str) -> "ProviderInfoResult":
        req = Request("GET", f"{self.BASE_URL}/series/{identifier}")
        result = self._request_page(req)
        data_map = {
            "name": None,
            "image": None,
            "genres": [],
            "synopsis": None,
            "release_year": None,
            "status": None,
            "alternative_names": [],
        }

        soup = BeautifulSoup(result.text, "html.parser")

        data_map["name"] = safe_attr(soup.find("h1"), "text")
        data_map["synopsis"] = safe_attr(
            soup.find("div", attrs={"class": "entry-content"}), "text"
        )
        data_map["image"] = safe_attr(
            soup.find("img", attrs={"class": "ts-post-image"}), "src"
        )
        data_map["genres"] = [
            safe_attr(i, "text")
            for i in soup.find_all("a", attrs={"href": re.compile(r"genre\/.+")})
        ]

        data = soup.find("span", attrs={"class": "spe"})
        if data is None:
            return ProviderInfoResult(**data_map)

        for d in data.find_all("span"):  # type: ignore
            title = safe_attr(d.find("b"), "text")
            desc = safe_attr(d, "text")
            if title is None or desc is None:
                continue

            if title == "Status:":
                data_map["status"] = Status[desc.strip().upper()]
            elif title == "Released:":
                try:
                    data_map["release_year"] = int(desc.strip())
                except (ValueError, TypeError):
                    pass

        return ProviderInfoResult(**data_map)

    def get_video(
        self, identifier: str, episode: "Episode", lang: LanguageTypeEnum
    ) -> List["ProviderStream"]:
        req = Request("GET", f"{self.BASE_URL}/{identifier}-episode-{episode}")
        res = self._request_page(req)
        soup = BeautifulSoup(res.text, 'html.parser')
        div_tag = soup.find('div', {'id': 'w-servers', 'class': 'bixbox'})
        video_data = {}
        types = soup.find_all('div', class_='type')
        for type_div in types:
            type_name=type_div['data-type']
            video_data[type_name] = []

            li_elements = type_div.find_all('li')
            if li_elements:
                for li in li_elements:
                    video_url = li.get('data-video')
                    video_label = li.get_text(strip=True)
                    if video_url:
                        video_data[type_name].append({'label': video_label, 'url': video_url})
        multi_provider="Vidhide"
        streams = video_data.get(lang.name, [])
        stream = next(filter(lambda x: x["label"] == multi_provider, streams), None)
        if stream is None:
            raise LangTypeNotAvailableError(identifier, self.NAME, lang)

        substreams = []
        req = Request("GET", stream["url"], headers={"referer": self.BASE_URL})
        res = self._request_page(req)
        soup = BeautifulSoup(res.text, 'html.parser')
        obsucated = str(soup.find('script', text=re.compile(r"eval\(function\(p,a,c,k,e,d\)")))
        def to_string(n,a):
            if n==0:
                return "0"
            digits = "0123456789abcdefghijklmnopqrstuvwxyz"
            result = []
            while n:
                result.append(digits[n % a])
                n //= a
            return ''.join(reversed(result))
        def dejs(p, a, c, k):
            while c > 0:
                c -= 1
                if k[c]:
                    p = re.sub(r'\b' + to_string(c,a) + r'\b', k[c], p)
            return p
        find_str="}('"
        parameter=obsucated.find(find_str)
        pattern = r"(?<!\\)'"
        segments = re.split(pattern, obsucated[parameter+len(find_str):])
        data = dejs(segments[0], int(segments[1].split(',')[1]), int(segments[1].split(',')[2]), segments[2].split('|'))
        url=re.search(r'file:"(https?://[^\s"]+)"', data).group(1)
        req = Request("GET", url)
        res = self._request_page(req)
        content = m3u8.M3U8(res.text, base_uri=urljoin(res.url, "."))
        if len(content.playlists) == 0:
            substreams.append(
                ProviderStream(
                    url=url,
                    resolution=1080,
                    episode=episode,
                    language=lang,
                    referrer=self.BASE_URL,
                )
            )

        for sub_playlist in content.playlists:
            substreams.append(
                ProviderStream(
                    url=urljoin(content.base_uri, sub_playlist.uri),
                    resolution=sub_playlist.stream_info.resolution[1],
                    episode=episode,
                    language=lang,
                    referrer=self.BASE_URL,
                )
            )
        return substreams
