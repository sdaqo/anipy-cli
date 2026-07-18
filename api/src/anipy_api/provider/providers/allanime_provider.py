import base64
import hashlib
import json
import re
import time
from copy import deepcopy
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple
from urllib.parse import urljoin

import Levenshtein
import m3u8
from anipy_api.provider import (
    BaseProvider,
    Episode,
    ProviderInfoResult,
    ProviderSearchResult,
    ProviderStream,
)
from anipy_api.provider.base import ExternalSub, InfoCallback, LanguageTypeEnum
from anipy_api.provider.filter import (
    BaseFilter,
    FilterCapabilities,
    Filters,
    MediaType,
    Season,
    Status,
)
from anipy_api.provider.utils import get_language_name, parsenum
from Cryptodome.Cipher import AES
from requests import Request, Session
from requests.exceptions import HTTPError

if TYPE_CHECKING:
    from anipy_api.provider import Episode


class AllAnimeCrypto:
    """Runtime handling of the AllAnime "aaReq" token.

    AllAnime signs the source-url query with an AES-GCM token whose epoch and
    key rotate every few days, and it expects a persisted-query hash that is
    the sha256 of the (assembled) source query. All of these live in the app js
    chunk / window.__aaCrypto, so they are fetched at runtime and cached,
    falling back to the last known good hardcoded values on failure.
    """

    MKISSA_URL = "https://mkissa.to/"
    CDN_IMMUTABLE = "https://cdn.allanime.day/all/mk/_app/immutable/"
    BROWSER_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    # Last known good values, only used when the runtime fetch fails.
    FALLBACK_EPOCH = 4130
    FALLBACK_MASK = "5264513ba898cb78c5c646bc1c12f2965a53a99891d91e83a2bf9244c36cca41"
    FALLBACK_PART_B = "nSMmjt8SIaRRj6ebdfimy1qXlUBuvMoBlPoUiSFoORg="
    FALLBACK_QUERY_HASH = (
        "d405d0edd690624b66baba3068e0edc3ac90f1597d898a1ec8db4e5c43c00fec"
    )
    # AllAnime encrypts the tobeparsed response with either the aaReq key or this static legacy key, depending on the rotation, so decoding tries both.
    RESPONSE_STATIC_KEY = hashlib.sha256(b"Xot36i3lK3:v1").digest()

    def __init__(self, info_callback: Optional[Callable[[str], None]] = None):
        self._info: Callable[[str], None] = info_callback or (lambda message: None)
        # (expires_ms, epoch, key, mask, query_hash) of the last successful fetch.
        self._cache: Optional[Tuple[float, int, bytes, str, str]] = None

    @staticmethod
    def _key(mask_hex: str, part_b: str) -> bytes:
        # AES-256 key: a hex "mask" xored with a base64 secret. The same key is
        # used for the aaReq token and for decrypting the tobeparsed response.
        return bytes(
            a ^ b for a, b in zip(bytes.fromhex(mask_hex), base64.b64decode(part_b))
        )

    @staticmethod
    def _source_query_hash(chunk_js: str) -> Optional[str]:
        """sha256 of the episode-sources GraphQL query.

        The query is a template literal in the chunk that interpolates other
        fragments (``${fragment}``) and a helper (``${helper()}``). We assemble
        it exactly like the site does and hash the result. Returns None if the
        template cannot be fully resolved, so the caller falls back.
        """
        template = next(
            (
                t
                for t in re.findall(r"`([^`]*)`", chunk_js)
                if "sourceUrls" in t and "episode(" in t
            ),
            None,
        )
        if template is None:
            return None

        def resolve(tmpl: str, depth: int = 0) -> str:
            if depth > 6:
                return tmpl
            for name in re.findall(r"\$\{([^}]+)\}", tmpl):
                if name.endswith("()"):
                    # ``helper = e => e ? `...` : `...` ``, called without an
                    # argument, so the else branch is used.
                    fn = re.search(
                        r"\b"
                        + re.escape(name[:-2])
                        + r"\s*=\s*\w+\s*=>\s*\w+\s*\?\s*`[^`]*`\s*:\s*`([^`]*)`",
                        chunk_js,
                    )
                    repl = fn.group(1) if fn else ""
                else:
                    var = re.search(
                        r"\b" + re.escape(name) + r"\s*=\s*`([^`]*)`", chunk_js
                    )
                    repl = resolve(var.group(1), depth + 1) if var else ""
                tmpl = tmpl.replace("${" + name + "}", repl)
            return tmpl

        query = resolve(template)
        if "${" in query:
            return None
        return hashlib.sha256(query.encode()).hexdigest()

    def _fetch(self, session: Session) -> Optional[Tuple[float, int, bytes, str, str]]:
        """Fetch (expires_ms, epoch, key, mask, query_hash) from the live site.

        epoch and partB are inlined as window.__aaCrypto on the frontend, the
        mask and the source query live in the app js chunk it imports.
        """
        headers = {"User-Agent": self.BROWSER_UA}
        try:
            html = session.get(self.MKISSA_URL, headers=headers, timeout=10).text
            aa = json.loads(
                re.search(r"window\.__aaCrypto\s*=\s*(\{.*?\})", html).group(1)
            )
            part_b, epoch = aa["partB"], aa["epoch"]
            expires = max(
                aa.get("switchAt", 0) + aa.get("graceMs", 0),
                time.time() * 1000 + 3600_000,
            )

            app = re.search(r"_app/immutable/(entry/app\.[^\"']+\.js)", html).group(1)
            app_js = session.get(
                self.CDN_IMMUTABLE + app, headers=headers, timeout=10
            ).text
            # The crypto chunk is one of the app's static imports and is the one
            # holding the 32 byte mask (a lone 64 char hex string).
            imports = re.findall(
                r"\s*[\"']\.\./(chunks/[A-Za-z0-9_\-]+\.js)[\"']", app_js
            )
            for chunk in imports:
                js = session.get(
                    self.CDN_IMMUTABLE + chunk, headers=headers, timeout=10
                ).text
                if "__aaCrypto" not in js:
                    continue
                masks = re.findall(r"[0-9a-f]{64}", js)
                if len(masks) == 1:
                    key = self._key(masks[0], part_b)
                    query_hash = self._source_query_hash(js) or self.FALLBACK_QUERY_HASH
                    return expires, int(epoch), key, masks[0], query_hash
            return None
        except Exception:
            return None

    def _current(self, session: Session) -> Tuple[int, bytes, str]:
        """Return (epoch, key, query_hash), fetching and caching it once."""
        if self._cache is None or self._cache[0] <= time.time() * 1000:
            fetched = self._fetch(session)
            if fetched is not None:
                self._cache = fetched
                self._info(
                    f"fetched aaReq crypto from site "
                    f"(epoch {fetched[1]}, hash {fetched[3][:8]})"
                )
            else:
                self._info("could not fetch aaReq crypto, using fallback values")
        if self._cache is not None:
            return self._cache[1], self._cache[2], self._cache[4]
        return (
            self.FALLBACK_EPOCH,
            self._key(self.FALLBACK_MASK, self.FALLBACK_PART_B),
            self.FALLBACK_QUERY_HASH,
        )

    def build_source_request(self, session: Session) -> Tuple[str, str, bytes]:
        """Build the episode-sources request crypto. Returns
        (query_hash, aaReq token, key), where the key is also needed to
        decrypt the tobeparsed response."""
        epoch, key, query_hash = self._current(session)
        # Timestamp is floored to a 5 minute window so it matches the server.
        ts = int(time.time() * 1000) // 300000 * 300000
        payload = {"v": 1, "ts": ts, "epoch": epoch, "qh": query_hash}
        # The iv is transmitted with the token, so it only has to be unique; the
        # server does not re-derive it (buildId used to sit in here).
        iv = hashlib.sha256(f"{epoch}:{query_hash}:{ts}".encode()).digest()[:12]
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(
            json.dumps(payload, separators=(",", ":")).encode()
        )
        token = base64.b64encode(b"\x01" + iv + ciphertext + tag).decode()
        return query_hash, token, key

    def invalidate(self):
        """Drop the cached crypto so the next request refetches it."""
        self._cache = None

    @staticmethod
    def decode_tobeparsed(tbp: str, key: bytes):
        raw = base64.b64decode(tbp)
        iv, ciphertext, tag = raw[1:13], raw[13:-16], raw[-16:]

        # The response is signed with either the aaReq key or the static legacy key, so try both and use whichever authenticates.
        for candidate in (key, AllAnimeCrypto.RESPONSE_STATIC_KEY):
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

    def __init__(
        self,
        base_url_override: Optional[str] = None,
        info_callback: Optional[InfoCallback] = None,
    ):
        super().__init__(base_url_override, info_callback)
        self._crypto = AllAnimeCrypto(self._info_callback)

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
        query_hash, aareq, key = self._crypto.build_source_request(self.session)
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
            try:
                data = self._crypto.decode_tobeparsed(data["tobeparsed"], key)
            except ValueError:
                # Crypto rotated between the aaReq and the response, drop the cache so the next attempt refetches, and return no streams instead of crashing.
                self._crypto.invalidate()
                return streams

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
