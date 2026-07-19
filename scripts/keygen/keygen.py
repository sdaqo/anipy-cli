import re
import time
import base64
import hashlib
import requests
import json
from typing import Optional, Callable, Tuple
from Cryptodome.Cipher import AES

MKISSA_URL = "https://mkissa.to/"
CDN_IMMUTABLE = "https://cdn.allanime.day/all/mk/_app/immutable/"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

STATIC_KEY = "Xot36i3lK3:v1"

SESSION = requests.session()

def get_key(mask_hex: str, part_b: str) -> bytes:
    # AES-256 key: a hex "mask" xored with a base64 secret. The same key is
    # used for the aaReq token and for decrypting the tobeparsed response.
    return bytes(
        a ^ b for a, b in zip(bytes.fromhex(mask_hex), base64.b64decode(part_b))
    )

@staticmethod
def source_query_hash(chunk_js: str) -> Optional[str]:
    """sha256 of the episode-sources GraphQL query.

    The query is a template literal in the chunk that interpolates other
    fragments (``${fragment}``) and a helper (``${helper()}``). We assemble
    it exactly like the site does and hash the result. Returns None if the
    template cannot be fully resolved, so the caller falls back.
    """
    template = next(
        (
            t
            for t in re.findall(r"(\nquery\([^`]*)`", chunk_js)
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

def fetch():
    """Fetch (expires_ms, epoch, key, mask, query_hash) from the live site.

    epoch and partB are inlined as window.__aaCrypto on the frontend, the
    mask and the source query live in the app js chunk it imports.
    """
    headers = {"User-Agent": BROWSER_UA}
    try:
        html = SESSION.get(MKISSA_URL, headers=headers, timeout=10).text
        aa = json.loads(
            re.search(r"window\.__aaCrypto\s*=\s*(\{.*?\})", html).group(1)
        )
        part_b, epoch = aa["partB"], aa["epoch"]
        expires = max(
            aa.get("switchAt", 0) + aa.get("graceMs", 0),
            time.time() * 1000 + 3600_000,
        )

        app = re.search(r"_app/immutable/(entry/app\.[^\"']+\.js)", html).group(1)
        app_js = SESSION.get(
            CDN_IMMUTABLE + app, headers=headers, timeout=10
        ).text
        # The crypto chunk is one of the app's static imports and is the one
        # holding the 32 byte mask (a lone 64 char hex string).
        imports = re.findall(
            r"\s*[\"']\.\./(chunks/[A-Za-z0-9_\-]+\.js)[\"']", app_js
        )
        for chunk in imports:
            js = SESSION.get(
                CDN_IMMUTABLE + chunk, headers=headers, timeout=10
            ).text
            if "__aaCrypto" not in js:
                continue
            masks = re.findall(r"[0-9a-f]{64}", js)
            if len(masks) == 1:
                key = get_key(masks[0], part_b)
                query_hash = source_query_hash(js) # or FALLBACK_QUERY_HASH
                return expires, int(epoch), key.hex(), masks[0], query_hash
        return None
    except Exception:
        return None

def current():
    fetched = fetch()
    file = open("./keygen.json", "w")
    json.dump({
        "epoch": fetched[1],
        "key": fetched[2],
        "query_hash": fetched[4],
        "static_key": STATIC_KEY
    }, file)



if __name__ == "__main__":
    current()
    print(open("./keygen.json", "r").read())
