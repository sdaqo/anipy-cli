import re
import base64
import json
import m3u8
import functools
from urllib.parse import urlparse, parse_qsl, urlencode, urljoin
from requests import Request, Session
from Cryptodome.Cipher import AES
from bs4 import BeautifulSoup
from pathlib import Path
from typing import TYPE_CHECKING, List

from anipy_cli.provider import (
    BaseProvider,
    ProviderSearchResult,
    ProviderInfoResult,
    ProviderStream
)
from anipy_cli.error import BeautifulSoupLocationError
from anipy_cli.provider.utils import request_page, memoized_method, parsenum
from anipy_cli.config import Config

if TYPE_CHECKING:
    from anipy_cli.provider import Episode

@functools.lru_cache()
def _get_enc_keys(session: Session, embed_url: str):
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
    pad = lambda s: s + chr(len(s) % 16) * (16 - len(s) % 16)
    return base64.b64encode(
        AES.new(key, AES.MODE_CBC, iv=iv).encrypt(pad(data).encode())
    )


def _aes_decrypt(data, key, iv):
    return (
        AES.new(key, AES.MODE_CBC, iv=iv)
        .decrypt(base64.b64decode(data))
        .strip(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10")
    )


class GoGoProvider(BaseProvider):
    NAME = "gogoanime"
    BASE_URL = Config().gogoanime_url

    def get_search(self, query: str) -> List[ProviderSearchResult]:
        search_url = self.BASE_URL + f"/search.html?keyword={query}"

        req = Request("GET", search_url)
        res = request_page(self.session, req)
        soup = BeautifulSoup(res.content, "html.parser")

        pages = soup.find_all("a", attrs={"data-page": re.compile(r"^ *\d[\d ]*$")})
        if pages == None:
            raise BeautifulSoupLocationError("page count", search_url)

        pages = [x.get("data-page") for x in pages]
        pages = int(pages[-1]) if len(pages) > 0 else 1

        results = []

        for p in range(pages):
            req = Request("GET", f"{search_url}&page={p + 1}")
            res = request_page(self.session, req)
            soup = BeautifulSoup(res.content, "html.parser")
            links = soup.find_all("p", attrs={"class": "name"})
            if links == None:
                raise BeautifulSoupLocationError("query results", res.url)

            for link in links:
                name = link.text.replace("\n", "")
                dub = "(dub)" in name.lower()
                identifier = Path(
                    link.findChildren("a", recursive=False)[0].get("href")
                ).name

                results.append(ProviderSearchResult(identifier, name, dub))

        return results

    @memoized_method()
    def get_episodes(self, identifier: str) -> List['Episode']:
        req = Request("GET", f"{self.BASE_URL}/category/{identifier}")
        res = request_page(self.session, req)

        self.movie_id = re.search(
            r'<input.+?value="(\d+)" id="movie_id"', res.text
        ).group(1)

        req = Request(
            "GET",
            "https://ajax.gogocdn.net/ajax/load-list-episode",
            params={"ep_start": 0, "ep_end": 9999, "id": self.movie_id},
        )
        res = request_page(self.session, req)

        ep_list = [
            parsenum(
                re.search(
                    r"\d+([\.]\d+)?", x.find("div", attrs={"class": "name"}).text
                ).group(0)
            )
            for x in BeautifulSoup(res.text, "html.parser").find_all("li")
        ]
        ep_list.reverse()

        return ep_list

    @memoized_method()
    def get_info(self, identifier: str) -> 'ProviderInfoResult':
        req = Request("GET", f"{self.BASE_URL}/category/{identifier}")
        res = request_page(self.session, req)

        soup = BeautifulSoup(res.text, "html.parser")
        info_body = soup.find("div", {"class": "anime_info_body_bg"})

        if info_body == None:
            raise BeautifulSoupLocationError("anime info", res.url)

        name = info_body.find("h1").text
        image = info_body.find("img").get("src").__str__()
        other_info = info_body.find_all("p", {"class": "type"})

        synopsis = other_info[1].text.replace("\n", "")
        release_year = other_info[3].text.replace("Released: ", "")
        status = other_info[4].text.replace("\n", "").replace("Status: ", "")
        genres = [x["title"] for x in other_info[2].find_all("a")]

        return ProviderInfoResult(name, image, genres, synopsis, release_year, status)

    def get_video(self, identifier: str, episode: 'Episode') -> List['ProviderStream']:
        episode_url = (
            f"{self.BASE_URL}/{identifier}-episode-{str(episode).replace('.', '-')}"
        )

        req = Request("GET", episode_url)
        res = request_page(self.session, req)

        soup = BeautifulSoup(res.content, "html.parser")
        link = soup.find("a", {"class": "active", "rel": "1"})

        if link == None:
            raise BeautifulSoupLocationError("embed url", res.url)

        embed_url: str = link["data-video"]

        req = Request("GET", embed_url)
        res = request_page(self.session, req)

        soup = BeautifulSoup(res.content, "html.parser")
        crypto = soup.find("script", {"data-name": "episode"})

        if crypto == None:
            raise BeautifulSoupLocationError("crypto", res.url)

        crypto = crypto["data-value"]

        parsed = urlparse(embed_url)
        ajax_url = f"{parsed.scheme}://{parsed.netloc}/encrypt-ajax.php?"

        enc_keys = _get_enc_keys(self.session, embed_url)
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
        res = request_page(self.session, req)

        json_res = json.loads(
            _aes_decrypt(res.json().get("data"), enc_keys["second_key"], enc_keys["iv"])
        )

        source_data = [x for x in json_res["source"]]

        streams = []
        for s in source_data:
            if s["type"] == "hls":
                req = Request("GET", s["file"])
                res = request_page(self.session, req)
                content = m3u8.M3U8(res.text, base_uri=urljoin(res.url, "."))
                if len(content.playlists) == 0:
                    streams.append(
                        ProviderStream(url=s["file"], resolution=1080, episode=episode)
                    )

                for playlist in content.playlists:
                    streams.append(
                        ProviderStream(
                            url=urljoin(content.base_uri, playlist.uri),
                            resolution=playlist.stream_info.resolution[1],
                            episode=episode,
                        )
                    )
            else:
                resolution = int(re.search(r"\d+", s["label"]).group(0))
                streams.append(
                    ProviderStream(
                        url=s["file"], resolution=resolution, episode=episode
                    )
                )

        return streams
