import base64
import functools
import hashlib
import json
import re
import time
from copy import deepcopy
from typing import TYPE_CHECKING, List, Optional, Tuple
from urllib.parse import urljoin

import Levenshtein
import m3u8
from anipy_api.provider import (BaseProvider, Episode, ProviderInfoResult,
                                ProviderSearchResult, ProviderStream)
from anipy_api.provider.base import ExternalSub, InfoCallback, LanguageTypeEnum
from anipy_api.provider.filter import (BaseFilter, FilterCapabilities, Filters,
                                       MediaType, Season, Status)
from anipy_api.provider.utils import get_language_name, parsenum, request_page
from Cryptodome.Cipher import AES
from requests import Request, Session
from requests.exceptions import HTTPError

if TYPE_CHECKING:
    from anipy_api.provider import Episode

KEYGEN_URL: str = (
    "https://raw.githubusercontent.com/sdaqo/anipy-cli/refs/heads/key-gen/scripts/keygen/keygen.json"
)

@functools.lru_cache()
def fetch_keygen(session: Session):
    req = Request("GET", KEYGEN_URL)
    res = request_page(session, req)
    return json.loads(res.text)



def build_source_request(session: Session) -> Tuple[str, str, str, str]:
    keygen = fetch_keygen(session)

    ts = int(time.time() * 1000) // 300000 * 300000
    payload = {
        "v": 1,
        "ts": ts,
        "epoch": keygen["epoch"],
        "buildId": keygen["build_id"],
        "qh": keygen["query_hash"],
        "k": keygen["lane"],
    }

    iv = hashlib.sha256(f"{keygen['epoch']}:{keygen['query_hash']}:{ts}".encode()).digest()[:12]
    cipher = AES.new(bytes.fromhex(keygen["key"]), AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(
        json.dumps(payload, separators=(",", ":")).encode()
    )
    token = base64.b64encode(b"\x01" + iv + ciphertext + tag).decode()

    return keygen["query_hash"], token, keygen["lane"], keygen["build_id"]


def decode_tobeparsed(session: Session, tbp: str):
    keygen = fetch_keygen(session)

    raw = base64.b64decode(tbp)
    iv, ciphertext, tag = raw[1:13], raw[13:-16], raw[-16:]

    # The response is signed with either the aaReq key or the static legacy key, so try both and use whichever authenticates.
    for candidate in (bytes.fromhex(keygen["key"]), keygen["static_key"]):
        try:
            cipher = AES.new(candidate, AES.MODE_GCM, nonce=iv)
            plain = cipher.decrypt_and_verify(ciphertext, tag)
            return json.loads(plain.decode("utf-8"))
        except ValueError:
            continue
    raise ValueError("tobeparsed could not be decrypted with any known key")


class AllAnimeFilter(BaseFilter):
    def _apply_query(self, query: str):
        if not query:
            return
        self._request.json["variables"]["search"].update({"query": query})

    def _apply_year(self, year: int):
        self._request.json["variables"]["search"].update({"year": int(year)})

    def _apply_season(self, season: Season):
        season_name = season.name.capitalize()
        self._request.json["variables"]["search"].update({"season": season_name})

    def _apply_status(self, status: Status): ...

    def _apply_media_type(self, media_type: MediaType):
        mapping = {
            MediaType.TV: "TV",
            MediaType.SPECIAL: "Special",
            MediaType.MOVIE: "Movie",
            MediaType.OVA: "OVA",
            MediaType.ONA: "ONA",
        }
        self._request.json["variables"]["search"].update(
            {"types": [mapping[media_type]]}
        )


class AllAnimeProvider(BaseProvider):
    """For detailed documentation have a look
    at the [base class][anipy_api.provider.base.BaseProvider].

    Attributes:
        NAME: allanime
        BASE_URL: https://mkissa.to
        FILTER_CAPS: YEAR, MEDIA_TYPE, SEASON, NO_QUERY
    """

    NAME: str = "allanime"
    BASE_URL: str = "https://mkissa.to"
    FILTER_CAPS: FilterCapabilities = (
        FilterCapabilities.YEAR
        | FilterCapabilities.MEDIA_TYPE
        | FilterCapabilities.SEASON
        | FilterCapabilities.NO_QUERY
    )

    API_URL: str = "https://api.mkissa.net/api"

    def __init__(
        self,
        base_url_override: Optional[str] = None,
        info_callback: Optional[InfoCallback] = None,
    ):
        super().__init__(base_url_override, info_callback)

    def get_search(
        self, query: str, filters: "Filters" = Filters()
    ) -> List[ProviderSearchResult]:
        req = Request(
            "POST",
            self.API_URL,
            json={
                "variables": {
                    "search": {},
                    "limit": 26,
                    "page": 1,
                    "translationType": "sub",
                    "countryOrigin": "ALL",
                },
                "extensions": json.dumps(
                    {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": "a24c500a1b765c68ae1d8dd85174931f661c71369c89b92b88b75a725afc471c",
                        }
                    }
                ),
            },
            headers={"Referer": "https://allmanga.to/"},
        )
        req = AllAnimeFilter(req).apply(query, filters)
        results = []
        page = 1
        while True:
            req.json["variables"]["page"] = page
            final_req = deepcopy(req)
            final_req.params["variables"] = json.dumps(final_req.json["variables"])
            res = self._request_page(final_req).json()
            provider_results = res["data"]["shows"]["edges"]
            if len(provider_results) == 0:
                break

            for a in provider_results:
                name = a["name"]
                identifier = a["_id"]
                languages = {LanguageTypeEnum.SUB}
                if a["availableEpisodes"].get("dub", 0) > 0:
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
            reverse=True,
        )

        return results

    def _request_page(self, req: Request):
        """Prepare a request and send it, but create a new session if self.session is broken and handle timeout error

        Args:
            req: The request

        Returns:
            out: Response of the request
        """

        response = super()._request_page(req)

        response_json = response.json()

        if "errors" in response_json:
            errors: list[dict] = response_json["errors"]

            # only handle the first error for now
            error_msg: str = errors[0]["message"]

            if error_msg.startswith("Too many requests,"):
                timeout = int(
                    error_msg.removeprefix(
                        "Too many requests, please try again in "
                    ).removesuffix(" seconds.")
                )
                time.sleep(timeout)
                return self._request_page(req)
            else:
                raise ConnectionError(
                    f"Server responded with unknown error: {error_msg}"
                )

        else:
            return response

    def get_episodes(self, identifier: str, lang: LanguageTypeEnum) -> List[Episode]:
        req = Request(
            "POST",
            self.API_URL,
            json={
                "variables": json.dumps({"_id": identifier}),
                "extensions": json.dumps(
                    {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": "043448386c7a686bc2aabfbb6b80f6074e795d350df48015023b079527b0848a",
                        }
                    }
                ),
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
            "POST",
            self.API_URL,
            json={
                "variables": json.dumps({"_id": identifier}),
                "extensions": json.dumps(
                    {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": "043448386c7a686bc2aabfbb6b80f6074e795d350df48015023b079527b0848a",
                        }
                    }
                ),
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
        query_hash, aareq, lane, build_id = build_source_request(self.session)
        # The source query has to go through as a GET request with the aaReq
        # token in the query string, otherwise the api returns AA_CRYPTO_MISSING.
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
                "extensions": json.dumps(
                    {
                        "persistedQuery": {
                            "version": 1,
                            "sha256Hash": query_hash,
                        },
                        "aaReq": aareq,
                        "k": lane
                    }
                ),
            },
            headers={
                "Referer": "https://mkissa.to",
                "Origin": "https://mkissa.to",
                "x-build-id": build_id,
            },
        )
        result = self._request_page(req).json()
        providers = ["Yt-mp4", "S-Mp4", "Uv-mp4", "Luf-Mp4", "Ak", "Default", "Mp4"]
        streams = []

        data = result.get("data") or {}
        if "tobeparsed" in data:
            try:
                data = decode_tobeparsed(self.session, data["tobeparsed"])
            except ValueError:
                # Crypto rotated between the aaReq and the response, drop the cache so the next attempt refetches, and return no streams instead of crashing.
                fetch_keygen.cache_clear()
                return streams

        if not data.get("episode"):
            return streams

        for provider in data["episode"]["sourceUrls"]:
            if provider["sourceName"] not in providers:
                continue

            if provider["sourceName"] == "Mp4":
                try:
                    response = request_page(
                        self.session, Request("GET", provider["sourceUrl"])
                    )
                except HTTPError:
                    continue
                if link := re.search(r'src:\s*"([^"]+)"', response.text):
                    streams.append(
                        ProviderStream(
                            link.group(1),
                            1080,
                            episode,
                            lang,
                            referrer="https://www.mp4upload.com",
                        )
                    )
                continue

            if "tools.fast4speed.rsvp" in provider["sourceUrl"]:
                streams.append(
                    ProviderStream(
                        url=provider["sourceUrl"],
                        resolution=1080,
                        episode=episode,
                        language=lang,
                        referrer=self.BASE_URL,
                    )
                )
                continue

            decrypted_path = self._decrypt(
                provider["sourceUrl"].replace("--", "")
            ).replace("clock", "clock.json")
            req = Request(
                "GET",
                f"https://allanime.day{decrypted_path}",
                headers={"Referer": "https://allanime.day/"},
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
    def _decrypt(provider_id: str) -> str:
        decrypted = ""
        for hex_value in [
            provider_id[i : i + 2] for i in range(0, len(provider_id), 2)
        ]:
            dec = int(hex_value, 16)
            xor = dec ^ 56
            oct_value = oct(xor)[2:].zfill(3)
            decrypted += chr(int(oct_value, 8))
        return decrypted
