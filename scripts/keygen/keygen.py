import re
import os
from subprocess import Popen
import subprocess
import time
import base64
import hashlib
import requests
import hmac
import json

MKISSA_URL = "https://mkissa.to/"
MKISSA_API_URL = "https://api.mkissa.net"
CDN_IMMUTABLE = "https://cdn.mkissa.net/all/mk/_app/immutable"
BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

STATIC_KEY = "Xot36i3lK3:v1"

SESSION = requests.session()

def get_crypto_mask(chunk_js: str):
    git_clone = Popen(["git", "clone", "https://github.com/mbpowers/ani-extract", "./ani-extract"])
    git_clone.wait()

    fp = open("./ani-extract/chunk.js", "w")
    fp.write(chunk_js)
    fp.close()

    npm_i = Popen(["npm", "i"], cwd="./ani-extract", stdout=subprocess.PIPE)
    npm_i.wait()
    node_run = Popen(
        ["node", "ani-extract.js", "./chunk.js"],
        cwd="./ani-extract", 
        stdout=subprocess.PIPE
    )
    node_run.wait()
    
    out, _ = node_run.communicate()
    return json.loads(out.decode("utf-8").strip().replace("'", "\""))

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
    html = SESSION.get(MKISSA_URL, headers=headers, timeout=10).text
    app_url = CDN_IMMUTABLE + re.search(
        r"/entry/app\.[A-Za-z0-9_.-]+\.js", html
    ).group()

    app_js = SESSION.get(app_url, headers=headers, timeout=10).text
    chunks = re.findall(r'"../(chunks/[A-Za-z0-9_.-]+\.js)"', app_js)[:5]
    for chunk in chunks:
        chunk_js = SESSION.get(f"{CDN_IMMUTABLE}/{chunk}", headers=headers).text
        if not ("VaildTranslationTypeEnumType" in chunk_js or "x-aa-boot" in chunk_js):
            continue

        build_id = re.search(r'!=="string"\?"([0-9]+)"', chunk_js).group(1)
        lane = re.search(r'const ..="(k[0-9]+)"', chunk_js).group(1)
        now_ms = int(time.time() * 1000)
        epoch = now_ms // 259_200_000
        if now_ms - epoch * 259_200_000 < 86_400_000 and epoch > 0:
            epoch -= 1

        crypto_mask_blocks = get_crypto_mask(chunk_js)
        embedded = b"".join(base64.b64decode(block) for block in crypto_mask_blocks)
        mask = bytes(
            value
            ^ (ord(build_id[index % len(build_id)]) ^ ((index * 17 + 31) & 0xFF))
            ^ ((index // 8 * 41 + index % 8 * 7) & 0xFF)
            for index, value in enumerate(embedded)
        )
        hmac_key = hmac.digest(mask, f"aa-boot:{build_id}".encode(), "sha256")
        aa_boot = hmac.digest(
            hmac_key,
            f"{build_id}:mkissa:mkissa.to:{epoch}:{lane}".encode(),
            "sha256",
        ).hex()

        bootstrap = SESSION.get(f"{MKISSA_API_URL}/client-crypto/v1/bootstrap",
            params={"buildId": build_id, "k": lane},
            headers={
                "x-build-id": build_id,
                "x-aa-boot": aa_boot,
                "Referer": MKISSA_URL,
                "Origin": MKISSA_URL,
                "User-Agent": BROWSER_UA
            },
        ).json()

        key = bytes(a ^ b for a, b in zip(mask, base64.b64decode(bootstrap["partB"])))

        query_hash = source_query_hash(chunk_js)

        return build_id, bootstrap["epoch"], bootstrap.get("k", lane), key.hex(), query_hash

if __name__ == "__main__":
    fetched = fetch()
    file = open("./keygen.json", "w")
    json.dump({
        "build_id": fetched[0],
        "epoch": fetched[1],
        "lane": fetched[2],
        "key": fetched[3],
        "query_hash": fetched[4],
        "static_key": STATIC_KEY,
    }, file)
