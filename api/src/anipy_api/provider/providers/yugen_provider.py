import base64
import re
from typing import TYPE_CHECKING, List
from urllib.parse import urljoin

import m3u8
from bs4 import BeautifulSoup
from requests import Request

from anipy_api.error import LangTypeNotAvailableError
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


class YugenFilter(BaseFilter):
    def _apply_query(self, query: str):
        self._request.params.update({"q": query})

    def _apply_year(self, year: int):
        self._request.params.update({"year": year})

    def _apply_season(self, season: Season):
        mapping = {v: k.capitalize() for k, v in Season._member_map_.items()}
        self._request.params.update({"season": mapping[season]})

    def _apply_status(self, status: Status):
        mapping = {
            Status.COMPLETED: "Finished Airing",
            Status.UPCOMING: "Not yet aired",
            Status.ONGOING: "Currently Airing",
        }
        self._request.params.update({"status": mapping[status]})

    def _apply_media_type(self, media_type: MediaType):
        mapping = {
            MediaType.TV: "TV",
            MediaType.SPECIAL: "Special",
            MediaType.MOVIE: "Movie",
            MediaType.OVA: "OVA",
            MediaType.ONA: "ONA",
            MediaType.MUSIC: "Music",
        }
        self._request.params.update({"type": mapping[media_type]})


class YugenProvider(BaseProvider):
    """For detailed documentation have a look
    at the [base class][anipy_api.provider.base.BaseProvider].

    Attributes:
        NAME: yugenanime
        BASE_URL: https://yugenanime.tv
        FILTER_CAPS: YEAR, SEASON, STATUS, MEDIA_TYPE, NO_QUERY
    """

    NAME: str = "yugenanime"
    BASE_URL: str = "https://yugenanime.tv"
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
        search_url = self.BASE_URL + "/api/discover/"
        req = Request("GET", search_url)
        req = YugenFilter(req).apply(query, filters)

        results = []
        has_next = True
        page = 0
        while has_next:
            req.params["page"] = page + 1
            res = self._request_page(req).json()
            has_next = res["hasNext"]

            soup = BeautifulSoup(res.get("query"), "html.parser")
            anime = soup.find_all("a", attrs={"class": "anime-meta"})
            id_regex = re.compile(r"(\d+)\/([^\/]+)")
            for a in anime:
                uri = a["href"]
                identifier = id_regex.search(uri)
                if identifier is None:
                    continue

                if len(identifier.groups()) != 2:
                    continue

                identifier = base64.b64encode(
                    f"{identifier.group(1)}/{identifier.group(2)}".encode()
                ).decode()

                name = a["title"]
                languages = {LanguageTypeEnum.SUB}
                excl = a.find("div", attrs={"class": "ani-exclamation"})
                if excl is not None:
                    if "dub" in excl.text.lower():
                        languages.add(LanguageTypeEnum.DUB)

                results.append(
                    ProviderSearchResult(
                        identifier=identifier, name=name, languages=languages
                    )
                )

            page += 1
        return results

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List["Episode"]:
        identifier = base64.b64decode(identifier).decode()
        req = Request("GET", f"{self.BASE_URL}/anime/{identifier}")
        result = self._request_page(req)

        if lang == LanguageTypeEnum.SUB:
            match = re.search(
                r'<div class="ap-.+?">Episodes</div><span class="description" .+?>(\d+)</span></div>',
                result.text,
            )
        else:
            match = re.search(
                r'<div class="ap-.+?">Episodes \(Dub\)</div><span class="description" .+?>(\d+)</span></div>',
                result.text,
            )

        if match is None:
            raise LangTypeNotAvailableError(identifier, self.NAME, lang)

        eps = int(match.group(1))
        return list(range(1, eps + 1))

    def get_info(self, identifier: str) -> "ProviderInfoResult":
        identifier = base64.b64decode(identifier).decode()
        req = Request("GET", f"{self.BASE_URL}/anime/{identifier}")
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

        name = soup.find("h1")
        if name is not None:
            data_map["name"] = name.get_text().strip()

        synopsis = soup.find("p", attrs={"class": "description"})
        if synopsis is not None:
            data_map["synopsis"] = synopsis.get_text("\n")

        image = soup.find("img", attrs={"class": "cover"})
        if image is not None:
            data_map["image"] = image.get("src")  # type: ignore

        data = soup.find_all("div", attrs={"class": "data"})
        for d in data:
            title = d.find("div")
            desc = d.find("span")
            if title is None or desc is None:
                continue
            title = title.text
            desc = desc.text
            if title in ["Native", "Romaji"]:
                data_map["alternative_names"].append(desc)
            elif title == "Synonyms":
                data_map["alternative_names"].extend(desc.split(","))
            elif title == "Premiered":
                try:
                    data_map["release_year"] = int(desc.split()[-1])
                except (ValueError, TypeError):
                    pass
            elif title == "Status":
                mapping = {
                    "Finished Airing": Status.COMPLETED,
                    "Not yet aired": Status.UPCOMING,
                    "Currently Airing": Status.ONGOING,
                }
                data_map["status"] = mapping.get(desc, None)
            elif title == "Genres":
                data_map["genres"].extend([g.strip() for g in desc.split(",")])

        return ProviderInfoResult(**data_map)

    def get_video(
        self, identifier: str, episode: "Episode", lang: LanguageTypeEnum
    ) -> List["ProviderStream"]:
        identifier = base64.b64decode(identifier).decode()

        id_num, _ = identifier.split("/")
        if lang == LanguageTypeEnum.DUB:
            video_query = f"{id_num}|{episode}|dub"
        else:
            video_query = f"{id_num}|{episode}"

        req = Request(
            "POST",
            f"{self.BASE_URL}/api/embed/",
            data={
                "id": base64.b64encode(video_query.encode()).decode(),
                "ac": "0",
            },
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        res = self._request_page(req)
        res = res.json()
        streams = []
        for playlist in res["hls"]:
            req = Request("GET", playlist)
            res = self._request_page(req)
            content = m3u8.M3U8(res.text, base_uri=urljoin(res.url, "."))
            if len(content.playlists) == 0:
                streams.append(
                    ProviderStream(
                        url=playlist,
                        resolution=1080,
                        episode=episode,
                        language=lang,
                    )
                )

            for sub_playlist in content.playlists:
                streams.append(
                    ProviderStream(
                        url=urljoin(content.base_uri, sub_playlist.uri),
                        resolution=sub_playlist.stream_info.resolution[1],
                        episode=episode,
                        language=lang,
                    )
                )
        return streams
