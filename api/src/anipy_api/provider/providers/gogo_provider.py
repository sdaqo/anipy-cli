import base64
import functools
import json
import re
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Tuple
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse

import m3u8
from bs4 import BeautifulSoup
from Cryptodome.Cipher import AES
from requests import Request
from requests.exceptions import HTTPError, ConnectionError as RequestConnectionError

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
from anipy_api.provider.utils import parsenum, request_page, safe_attr

if TYPE_CHECKING:
    from anipy_api.provider import Episode
    from requests import Session


@functools.lru_cache()
def _get_enc_keys(session: "Session", embed_url: str):
    # This method is outside of the main class
    # so the cache is not bound to the class
    # instance
    page = request_page(session, Request("GET", embed_url)).text

    keys = re.findall(r"(?:container|videocontent)-(\d+)", page)

    if not keys:
        return {}

    key, iv, second_key = keys

    return {
        "key": key.encode(),
        "second_key": second_key.encode(),
        "iv": iv.encode(),
    }


def _aes_encrypt(data, key, iv):
    def pad(s):
        return s + chr(len(s) % 16) * (16 - len(s) % 16)

    return base64.b64encode(
        AES.new(key, AES.MODE_CBC, iv=iv).encrypt(pad(data).encode())
    )


def _aes_decrypt(data, key, iv):
    return (
        AES.new(key, AES.MODE_CBC, iv=iv)
        .decrypt(base64.b64decode(data))
        .strip(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10")
    )


class GoGoFilter(BaseFilter):
    def _apply_query(self, query: str):
        self._request.params.update({"keyword": query})

    def _apply_year(self, year: int):
        self._request.params.update({"year[]": [year]})

    def _apply_season(self, season: Season):
        mapping = {v: k.lower() for k, v in Season._member_map_.items()}
        self._request.params.update({"season[]": [mapping[season]]})

    def _apply_status(self, status: Status):
        mapping = {v: k.capitalize() for k, v in Status._member_map_.items()}
        self._request.params.update({"status[]": [mapping[status]]})

    def _apply_media_type(self, media_type: MediaType):
        # I have found that gogo's media type filter is not very accurate
        # will leave the code here for the time they fix it...
        # mapping = {
        #     MediaType.TV: 1,
        #     MediaType.SPECIAL: 2,
        #     MediaType.MOVIE: 3,
        #     MediaType.OVA: 26,
        #     MediaType.ONA: 30,
        #     MediaType.MUSIC: 32
        # }
        # self._request.params.update(
        #     {"type[]": self._map_enum_members(media_type, mapping)}
        # )
        ...


class GoGoProvider(BaseProvider):
    """For detailed documentation have a look
    at the [base class][anipy_api.provider.base.BaseProvider].

    Attributes:
        NAME: gogoanime
        BASE_URL: https://gogoanime3.co
        FILTER_CAPS: YEAR, SEASON, STATUS, NO_QUERY
    """

    NAME: str = "gogoanime"
    BASE_URL: str = "https://gogoanime3.co"
    FILTER_CAPS: FilterCapabilities = (
        FilterCapabilities.YEAR
        | FilterCapabilities.SEASON
        | FilterCapabilities.STATUS
        | FilterCapabilities.NO_QUERY
    )

    def get_search(
        self, query: str, filters: "Filters" = Filters()
    ) -> List[ProviderSearchResult]:
        search_url = self.BASE_URL + "/filter.html"
        req = Request("GET", search_url)
        req = GoGoFilter(req).apply(query, filters)

        res = self._request_page(req)
        soup = BeautifulSoup(res.content, "html.parser")

        pages = soup.find_all("a", attrs={"data-page": re.compile(r"^ *\d[\d ]*$")})
        if pages is None:
            raise BeautifulSoupLocationError("page count", search_url)

        pages = [x.get("data-page") for x in pages]
        pages = int(pages[-1]) if len(pages) > 0 else 1

        results: Dict[str, ProviderSearchResult] = {}

        for p in range(pages):
            req.params["page"] = p + 1
            res = self._request_page(req)
            soup = BeautifulSoup(res.content, "html.parser")
            links = soup.find_all("p", attrs={"class": "name"})
            if links is None:
                raise BeautifulSoupLocationError("query results", res.url)

            for link in links:
                name = link.text.replace("\n", "")
                name = re.sub(
                    r"\s?\((dub|japanese\sdub)\)", "", name, flags=re.IGNORECASE
                )

                identifier = Path(
                    link.findChildren("a", recursive=False)[0].get("href")
                ).name

                if identifier.endswith("-dub"):
                    identifier = identifier.removesuffix("-dub")
                    identifier = identifier.removesuffix("-japanese-dub")
                    if identifier not in results:
                        results[identifier] = ProviderSearchResult(
                            identifier, name, languages={LanguageTypeEnum.DUB}
                        )
                    else:
                        results[identifier].languages.add(LanguageTypeEnum.DUB)
                else:
                    if identifier not in results:
                        results[identifier] = ProviderSearchResult(
                            identifier, name, languages={LanguageTypeEnum.SUB}
                        )
                    else:
                        results[identifier].languages.add(LanguageTypeEnum.SUB)

        return list(results.values())

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List["Episode"]:
        ep_list = self._get_episode_ajax(identifier, lang)
        return [e[1] for e in ep_list]

    def get_info(self, identifier: str) -> "ProviderInfoResult":
        req = Request("GET", f"{self.BASE_URL}/category/{identifier}")
        res = self._request_page(req)

        soup = BeautifulSoup(res.text, "html.parser")
        info_body = soup.find("div", {"class": "anime_info_body_bg"})

        if info_body is None:
            raise BeautifulSoupLocationError("anime info", res.url)

        name = safe_attr(info_body.find("h1"), "text")
        image = safe_attr(info_body.find("img"), "src")

        alt_names = info_body.find("p", {"class": "other-name"})  # type: ignore
        if alt_names is not None:
            alt_names = safe_attr(alt_names.find("a"), "text").split(",")  # type: ignore
        synopsis = safe_attr(info_body.find("div", {"class": "description"}), "text").replace("\n", "")  # type: ignore

        other_info = info_body.find_all("p", {"class": "type"})  # type: ignore
        status, release_year, genres = None, None, []
        for i in other_info:
            cat_name = safe_attr(i.find("span"), "text")

            if cat_name == "Genre:":
                genres = [x["title"] for x in i.find_all("a")]
            elif cat_name == "Status:":
                status = safe_attr(i.find("a"), "text")
                try:
                    status = Status[status.upper()]  # type: ignore
                except KeyError:
                    status = None
            elif cat_name == "Released:":
                try:
                    release_year = int(safe_attr(i, "text").replace("Released: ", ""))  # type: ignore
                except (ValueError, TypeError):
                    release_year = None

        return ProviderInfoResult(
            name, image, genres, synopsis, release_year, status, alt_names
        )

    def get_video(
        self, identifier: str, episode: "Episode", lang: LanguageTypeEnum
    ) -> List["ProviderStream"]:
        ep_str = str(episode).replace(".", "-")
        if lang == LanguageTypeEnum.DUB:
            urls = [
                f"{self.BASE_URL}/{identifier}-dub-episode-{ep_str}",
                f"{self.BASE_URL}/{identifier}-japanese-dub-episode-{ep_str}",
            ]
        else:
            urls = [f"{self.BASE_URL}/{identifier}-episode-{ep_str}"]

        res = None
        for u in urls:
            try:
                req = Request("GET", u)
                res = self._request_page(req)
                break
            except HTTPError:
                continue

        if res is None:
            # GoGo's is **very** inconsistent when it comes to naming,
            # so try one last time by querying the ajax, this should be very accurate but
            # pretty expensive, so it is a last resort.

            ajax_res = self._get_episode_ajax(identifier, lang)
            filtered_res = next(filter(lambda x: episode == x[1], ajax_res), None)

            if filtered_res is None:
                raise LangTypeNotAvailableError(identifier, self.NAME, lang)
            else:
                req = Request("GET", f"{self.BASE_URL}{filtered_res[0]}")
                res = self._request_page(req)

        soup = BeautifulSoup(res.content, "html.parser")
        link = soup.find("a", {"class": "active", "rel": "1"})

        if link is None:
            raise BeautifulSoupLocationError("embed url", res.url)

        embed_url: str = link["data-video"]

        req = Request("GET", embed_url)
        res = self._request_page(req)

        soup = BeautifulSoup(res.content, "html.parser")
        crypto = soup.find("script", {"data-name": "episode"})

        if crypto is None:
            raise BeautifulSoupLocationError("crypto", res.url)

        crypto = crypto["data-value"]

        parsed = urlparse(embed_url)
        ajax_url = f"{parsed.scheme}://{parsed.netloc}/encrypt-ajax.php?"

        enc_keys = self._get_enc_keys(embed_url)
        data = _aes_decrypt(crypto, enc_keys["key"], enc_keys["iv"]).decode()
        data = dict(parse_qsl(data))

        id_param = dict(parse_qsl(parsed.query))["id"]
        enc_id = _aes_encrypt(id_param, enc_keys["key"], enc_keys["iv"]).decode()
        data.update(id=enc_id)

        headers = {"x-requested-with": "XMLHttpRequest", "referer": embed_url}

        req = Request(
            "POST",
            ajax_url + urlencode(data) + f"&alias={id_param}",
            headers=headers,
        )
        res = self._request_page(req)

        json_res = json.loads(
            _aes_decrypt(res.json().get("data"), enc_keys["second_key"], enc_keys["iv"])
        )

        source_data = [x for x in json_res["source"]]

        streams = []
        for s in source_data:
            if s["type"] == "hls":
                req = Request("GET", s["file"])
                res = self._request_page(req)
                content = m3u8.M3U8(res.text, base_uri=urljoin(res.url, "."))
                if len(content.playlists) == 0:
                    streams.append(
                        ProviderStream(
                            url=s["file"],
                            resolution=1080,
                            episode=episode,
                            language=lang,
                        )
                    )

                for playlist in content.playlists:
                    streams.append(
                        ProviderStream(
                            url=urljoin(content.base_uri, playlist.uri),
                            resolution=playlist.stream_info.resolution[1],
                            episode=episode,
                            language=lang,
                        )
                    )
            else:
                resolution = int(re.search(r"\d+", s["label"]).group(0))
                streams.append(
                    ProviderStream(
                        url=s["file"],
                        resolution=resolution,
                        episode=episode,
                        language=lang,
                    )
                )

        return streams

    def _get_episode_ajax(
        self, identifier: str, lang: LanguageTypeEnum
    ) -> List[Tuple[str, "Episode"]]:
        if lang == LanguageTypeEnum.DUB:
            urls = [
                f"{self.BASE_URL}/category/{identifier}-dub",
                f"{self.BASE_URL}/category/{identifier}-japanese-dub",
            ]
        else:
            urls = [f"{self.BASE_URL}/category/{identifier}"]

        res = None
        for u in urls:
            try:
                req = Request("GET", u)
                res = self._request_page(req)
                break
            except HTTPError:
                continue

        if res is None:
            raise LangTypeNotAvailableError(identifier, self.NAME, lang)

        self.movie_id = re.search(
            r'<input.+?value="(\d+)" id="movie_id"', res.text
        ).group(1)

        req = Request(
            "GET",
            "https://ajax.gogocdn.net/ajax/load-list-episode",
            params={"ep_start": 0, "ep_end": 9999, "id": self.movie_id},
        )
        res = self._request_page(req)

        ep_list = [
            (
                x.find("a").get("href").strip(),
                parsenum(
                    re.search(
                        r"\d+([\.]\d+)?", x.find("div", attrs={"class": "name"}).text
                    ).group(0)
                ),
            )
            for x in BeautifulSoup(res.text, "html.parser").find_all("li")
        ]
        ep_list.reverse()

        return ep_list

    def _get_enc_keys(self, embed_url: str):
        try:
            return _get_enc_keys(self.session, embed_url)
        except RequestConnectionError:
            return _get_enc_keys(self._generate_new_session(), embed_url)
        