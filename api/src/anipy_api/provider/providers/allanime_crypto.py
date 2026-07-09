import base64
import hashlib
import json
import re
import time
from typing import Callable, Optional, Tuple

from requests import Session
from Cryptodome.Cipher import AES


class AllAnimeCrypto:
    """Runtime handling of the AllAnime "aaReq" token.

    AllAnime signs the source-url query with an AES-GCM token whose epoch and
    key rotate every few days. Those values live in window.__aaCrypto on the
    frontend and in the app js chunk it imports, so they are fetched at runtime
    and cached, falling back to the last known good hardcoded values on failure.
    """

    MKISSA_URL = "https://mkissa.to/"
    CDN_IMMUTABLE = "https://cdn.allanime.day/all/mk/_app/immutable/"
    BROWSER_UA = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
    )
    # buildId is not checked by the api, epoch has to match exactly.
    BUILD_ID = "9"
    # Last known good crypto, only used when the runtime fetch fails.
    FALLBACK_EPOCH = 4128
    FALLBACK_MASK = "b1a9a4d051988f1b1b12dbb747439d9bd64b09ea17835600a7eaa4de87c1ad87"
    FALLBACK_PART_B = "k7DLdv5SGiuEyGUtcncl5wQOR7r4aenLfDV3AOBKlAU="

    def __init__(self, info_callback: Optional[Callable[[str], None]] = None):
        self._info: Callable[[str], None] = info_callback or (lambda message: None)
        # (expires_ms, epoch, key, mask) of the last successful fetch.
        self._cache: Optional[Tuple[float, int, bytes, str]] = None

    @staticmethod
    def _key(mask_hex: str, part_b: str) -> bytes:
        # AES-256 key: a hex "mask" xored with a base64 secret. The same key is
        # used for the aaReq token and for decrypting the tobeparsed response.
        return bytes(
            a ^ b for a, b in zip(bytes.fromhex(mask_hex), base64.b64decode(part_b))
        )

    def _fetch(self, session: Session) -> Optional[Tuple[float, int, bytes, str]]:
        """Fetch (expires_ms, epoch, key, mask) from the live site, or None.

        epoch and partB are inlined as window.__aaCrypto on the frontend, the
        mask is a hex constant in the app js chunk it statically imports.
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
                r"(?:import|from)\s*[\"']\.\./(chunks/[A-Za-z0-9_\-]+\.js)[\"']", app_js
            )
            for chunk in imports:
                js = session.get(
                    self.CDN_IMMUTABLE + chunk, headers=headers, timeout=10
                ).text
                if "__aaCrypto" not in js:
                    continue
                masks = re.findall(r"[0-9a-f]{64}", js)
                if len(masks) == 1:
                    return expires, int(epoch), self._key(masks[0], part_b), masks[0]
            return None
        except Exception:
            return None

    def _current(self, session: Session) -> Tuple[int, bytes]:
        """Return the current (epoch, key), fetching and caching it once."""
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
            return self._cache[1], self._cache[2]
        return self.FALLBACK_EPOCH, self._key(self.FALLBACK_MASK, self.FALLBACK_PART_B)

    def build_aareq(self, session: Session, query_hash: str) -> Tuple[str, bytes]:
        """Build the aaReq token for a query. Returns (token, key), where the key
        is also needed to decrypt the tobeparsed response."""
        epoch, key = self._current(session)
        # Timestamp is floored to a 5 minute window so it matches the server.
        ts = int(time.time() * 1000) // 300000 * 300000
        payload = {
            "v": 1,
            "ts": ts,
            "epoch": epoch,
            "buildId": self.BUILD_ID,
            "qh": query_hash,
        }
        iv = hashlib.sha256(
            f"{epoch}:{self.BUILD_ID}:{query_hash}:{ts}".encode()
        ).digest()[:12]
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        ciphertext, tag = cipher.encrypt_and_digest(
            json.dumps(payload, separators=(",", ":")).encode()
        )
        token = base64.b64encode(b"\x01" + iv + ciphertext + tag).decode()
        return token, key

    @staticmethod
    def decode_tobeparsed(tbp: str, key: bytes):
        raw = base64.b64decode(tbp)
        iv, ciphertext, tag = raw[1:13], raw[13:-16], raw[-16:]
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv)
        return json.loads(cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8"))
