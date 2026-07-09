import json
import re
import time
from typing import TYPE_CHECKING, List, Optional, Tuple
from urllib.parse import urljoin

import hashlib
import base64
import m3u8
import Levenshtein
from requests import Request, Session
from requests.exceptions import HTTPError
from Cryptodome.Cipher import AES

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

# AllAnime protects the source-url query with an "aaReq" token that has to be
# sent inside the GraphQL extensions object, otherwise the api answers with
# AA_CRYPTO_MISSING. The token is AES-GCM encrypted with a key derived from an
# "epoch" and two secrets that the site rotates every few days. Those live in
# window.__aaCrypto on the frontend and in the app js chunk, so we fetch them
# at runtime (see _fetch_aa_crypto) and only fall back to these last-known-good
# values if that fails. buildId is not checked by the api.
_AAREQ_EPOCH = 4128
_AAREQ_BUILD_ID = "9"
_VIDEO_QUERY_HASH = "d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec"
_AAREQ_KEY_A = "b1a9a4d051988f1b1b12dbb747439d9bd64b09ea17835600a7eaa4de87c1ad87"
_AAREQ_KEY_B = "k7DLdv5SGiuEyGUtcncl5wQOR7r4aenLfDV3AOBKlAU="

_MKISSA_URL = "https://mkissa.to/"
_CDN_IMMUTABLE = "https://cdn.allanime.day/all/mk/_app/immutable/"
_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Cached (expires_ms, epoch, key) from the last successful runtime fetch.
_aa_crypto_cache: Optional[Tuple[float, int, bytes]] = None


def _xor_key(mask_hex: str, part_b: str) -> bytes:
    # AES-256 key: a hex "mask" xored with a base64 secret. The same key is used
    # for the aaReq token and for decrypting the tobeparsed response.
    return bytes(
        a ^ b for a, b in zip(bytes.fromhex(mask_hex), base64.b64decode(part_b))
    )


def _fetch_aa_crypto(session: Session) -> Optional[Tuple[float, int, bytes]]:
    """Fetch the current epoch and encryption key from the live site.

    epoch and partB are inlined as window.__aaCrypto on the frontend, the mask
    is a hex constant in the app js chunk it statically imports. Returns
    (expires_ms, epoch, key) or None if anything is unavailable.
    """
    try:
        html = session.get(
            _MKISSA_URL, headers={"User-Agent": _BROWSER_UA}, timeout=10
        ).text
        aa = json.loads(re.search(r"window\.__aaCrypto\s*=\s*(\{.*?\})", html).group(1))
        part_b, epoch = aa["partB"], aa["epoch"]
        expires = max(
            aa.get("switchAt", 0) + aa.get("graceMs", 0), time.time() * 1000 + 3600_000
        )

        app = re.search(r"_app/immutable/(entry/app\.[^\"']+\.js)", html).group(1)
        app_js = session.get(
            _CDN_IMMUTABLE + app, headers={"User-Agent": _BROWSER_UA}, timeout=10
        ).text
        # The crypto chunk is one of the app's static imports and is the one
        # holding the 32 byte mask (a lone 64 char hex string).
        imports = re.findall(
            r"(?:import|from)\s*[\"']\.\./(chunks/[A-Za-z0-9_\-]+\.js)[\"']", app_js
        )
        for chunk in imports:
            js = session.get(
                _CDN_IMMUTABLE + chunk, headers={"User-Agent": _BROWSER_UA}, timeout=10
            ).text
            if "__aaCrypto" not in js:
                continue
            masks = re.findall(r"[0-9a-f]{64}", js)
            if len(masks) == 1:
                return expires, int(epoch), _xor_key(masks[0], part_b)
        return None
    except Exception:
        return None


def _get_aa_crypto(session: Session) -> Tuple[int, bytes]:
    """Return the current (epoch, key), fetching and caching it once per run and
    falling back to the last-known-good hardcoded values on failure."""
    global _aa_crypto_cache
    if _aa_crypto_cache is None or _aa_crypto_cache[0] <= time.time() * 1000:
        _aa_crypto_cache = _fetch_aa_crypto(session) or _aa_crypto_cache
    if _aa_crypto_cache is not None:
        return _aa_crypto_cache[1], _aa_crypto_cache[2]
    return _AAREQ_EPOCH, _xor_key(_AAREQ_KEY_A, _AAREQ_KEY_B)


def _decode_tobeparsed(tbp: str, key: bytes):
    raw = base64.b64decode(tbp)
    iv, ciphertext, tag = raw[1:13], raw[13:-16], raw[-16:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    decrypted = cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")
    return json.loads(decrypted)


def _generate_aareq(query_hash: str, epoch: int, key: bytes) -> str:
    # Timestamp is floored to a 5 minute window so it matches the server clock.
    ts = int(time.time() * 1000) // 300000 * 300000
    payload = {
        "v": 1,
        "ts": ts,
        "epoch": epoch,
        "buildId": _AAREQ_BUILD_ID,
        "qh": query_hash,
    }
    iv = hashlib.sha256(
        f"{epoch}:{_AAREQ_BUILD_ID}:{query_hash}:{ts}".encode()
    ).digest()[:12]
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
    ciphertext, tag = cipher.encrypt_and_digest(
        json.dumps(payload, separators=(",", ":")).encode()
    )
    return base64.b64encode(b"\x01" + iv + ciphertext + tag).decode()


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
        epoch, key = _get_aa_crypto(self.session)
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
                            "sha256Hash": _VIDEO_QUERY_HASH,
                        },
                        "aaReq": _generate_aareq(_VIDEO_QUERY_HASH, epoch, key),
                    }
                ),
            },
            headers={"Referer": "https://youtu-chan.com/"},
        )
        result = self._request_page(req).json()
        providers = ["Yt-mp4", "S-Mp4", "Uv-mp4", "Ak", "Default"]
        streams = []

        data = result.get("data") or {}
        if "tobeparsed" in data:
            data = _decode_tobeparsed(data["tobeparsed"], key)

        if not data.get("episode"):
            return streams

        for provider in data["episode"]["sourceUrls"]:
            if provider["sourceName"] not in providers:
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
