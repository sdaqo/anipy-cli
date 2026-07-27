import re
import time
import base64
import hashlib
import requests
import json

MKISSA_URL = "https://mkissa.to/"
CRYPTO_URL = "https://api.mkissa.net/client-crypto/v1/bootstrap?buildId=72&k=k7"
CDN_IMMUTABLE = "https://cdn.allanime.day/all/mk/_app/immutable/"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

STATIC_KEY = "Xot36i3lK3:v1"

SESSION = requests.session()

@staticmethod
def source_query_hash(chunk_js: str):
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
                # ``helper = e => e ? `...` : `...` ``
                fn = re.search(
                    re.escape(name[:-2])
                    + r"\s*=\s*\w+\s*=>\s*\w+\s*\?\s*`[^`]*`\s*:\s*`([^`]*)`",
                    chunk_js,
                )
                repl = fn.group(1) if fn else ""
            else:
                var = re.search(
                    re.escape(name) + r"\s*=\s*`([^`]*)`", chunk_js
                )
                repl = resolve(var.group(1), depth + 1) if var else ""
            tmpl = tmpl.replace("${" + name + "}", repl)
        return tmpl

    query = resolve(template)
    if "${" in query:
        return None
    return hashlib.sha256(query.encode()).hexdigest()

def fetch():
    headers = {"User-Agent": BROWSER_UA}
    try:
        html = SESSION.get(MKISSA_URL, headers=headers, timeout=10).text
        aa_match = re.search(r"window\.__aaCrypto\s*=\s*(\{.*?\})", html)
        if aa_match:
            aa = json.loads(aa_match.group(1))
        else:
            crypto_headers = {
                "x-build-id": "72",
                "x-aa-boot": "221aca981efb2413205ad417d390f6ef494755bd958e131e29042111b0834e0a",
                "Referer": MKISSA_URL
            }
            crypto_headers.update(headers)

            res = SESSION.get(CRYPTO_URL, headers=crypto_headers)
            aa = res.json()
        k = aa["k"]
        part_b, epoch = aa["partB"], aa["epoch"]
        expires = max(
            aa.get("switchAt", 0) + aa.get("graceMs", 0),
            time.time() * 1000 + 3600_000,
        )

        app = re.search(r"_app/immutable/(entry/app\.[^\"']+\.js)", html).group(1)
        app_js = SESSION.get(
            CDN_IMMUTABLE + app, headers=headers, timeout=10
        ).text
        imports = re.findall(
            r"\s*[\"']\.\./(chunks/[A-Za-z0-9_\-]+\.js)[\"']", app_js
        )
        for chunk in imports:
            js = SESSION.get(
                CDN_IMMUTABLE + chunk, headers=headers, timeout=10
            ).text
            if "x-aa-boot" not in js:
                continue
            masks = ["221aca981efb2413205ad417d390f6ef494755bd958e131e29042111b0834e0a"] # re.findall(r"[0-9a-f]{64}", js)
            if len(masks) == 1:
                key = bytes(
                    a ^ b for a, b in zip(bytes.fromhex(masks[0]), base64.b64decode(part_b))
                )
                query_hash = source_query_hash(js)
                return expires, int(epoch), key.hex(), masks[0], query_hash, k
        return None
    except Exception as e:
        print(e)
        return None

if __name__ == "__main__":
    fetched = fetch()
    file = open("./keygen.json", "w")
    json.dump({
        "epoch": fetched[1],
        "key": fetched[2],
        "query_hash": fetched[4],
        "k": fetched[5],
        "static_key": STATIC_KEY,
    }, file)
