import sys
import json
import requests
import re
import base64
import functools
import m3u8
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urljoin
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from Cryptodome.Cipher import AES

from .misc import response_err, error, loc_err, parsenum
from .colors import colors
from .config import Config


class epHandler:
    """
    Class for handling episodes and stuff.
    Requires at least the category_url field of the
    entry to be filled.
    """

    def __init__(self, entry) -> None:
        self.entry = entry
        self.movie_id = None
        self.ep_list = None

    def get_entry(self):
        """
        Returns the entry with which was
        previously passed to this class.
        """
        return self.entry

    def _load_eps_list(self):
        if self.ep_list:
            return self.ep_list

        if not self.movie_id:
            r = requests.get(self.entry.category_url)
            self.movie_id = re.search(
                r'<input.+?value="(\d+)" id="movie_id"', r.text
            ).group(1)

        res = requests.get(
            "https://ajax.gogo-load.com/ajax/load-list-episode",
            params={"ep_start": 0, "ep_end": 9999, "id": self.movie_id},
        )

        response_err(res, res.url)
        ep_list = [
            {
                "ep": re.search(
                    r"\d+([\.]\d+)?", x.find("div", attrs={"class": "name"}).text
                ).group(0),
                "link": Config().gogoanime_url + x.find("a")["href"].strip(),
            }
            for x in BeautifulSoup(res.text, "html.parser").find_all("li")
        ]

        ep_list.reverse()

        self.ep_list = ep_list

        return ep_list

    def gen_eplink(self):
        """
        Generate episode url
        from ep and category url will look something like this:
        https://gogoanime.film/category/hyouka
        to
        https://gogoanime.film/hyouka-episode-1
        """
        ep_list = self._load_eps_list()

        filtered = list(filter(lambda x: x["ep"] == str(self.entry.ep), ep_list))

        if not filtered:
            error(f"Episode {self.entry.ep} does not exsist.")
            sys.exit()

        self.entry.ep_url = filtered[0]["link"]

        return self.entry

    def get_special_list(self):
        """
        Get List of Special Episodes (.5)
        """

        ep_list = self._load_eps_list()
        return list(filter(lambda x: re.match(r"^-?\d+(?:\.\d+)$", x["ep"]), ep_list))

    def get_latest(self):
        """
        Fetch latest episode avalible
        from a show and return it.
        """

        ep_list = self._load_eps_list()

        if not ep_list:
            self.entry.latest_ep = 0
            return 0
        else:
            latest = ep_list[-1]["ep"]
            self.entry.latest_ep = parsenum(latest)
            return parsenum(latest)

    def get_first(self):
        ep_list = self._load_eps_list()
        if not ep_list:
            return 0
        else:
            return ep_list[0]["ep"]

    def _create_prompt(self, prompt="Episode"):
        ep_range = f" [{self.get_first()}-{self.get_latest()}]"

        specials = self.get_special_list()
        if specials:
            ep_range += " Special Eps: "
            ep_range += ", ".join([x["ep"] for x in specials])

        return str(
            colors.END
            + prompt
            + colors.GREEN
            + ep_range
            + colors.END
            + "\n>> "
            + colors.CYAN
        )

    def _validate_ep(self, ep: str):
        """
        See if Episode is in episode list.
        Pass a arg to special to accept this
        charachter even though it is not in the episode list.
        """

        ep_list = self._load_eps_list()

        is_in_list = bool(list(filter(lambda x: ep == x["ep"], ep_list)))

        return is_in_list

    def pick_ep(self):
        """
        Cli function to pick a episode from 1 to
        the latest avalible.
        """

        self.get_latest()

        while True:
            which_episode = input(self._create_prompt())
            try:
                if self._validate_ep(which_episode):
                    self.entry.ep = parsenum(which_episode)
                    self.gen_eplink()
                    break
                else:
                    error("Number out of range.")

            except:
                error("Invalid Input")

        return self.entry

    def pick_ep_seasonal(self):
        """
        Cli function to pick a episode from 0 to
        the latest avalible.
        """

        self.get_latest()

        while True:
            which_episode = input(
                self._create_prompt(
                    "Last Episode you watched (put 0 to start at the beginning) "
                )
            )
            try:
                if self._validate_ep(which_episode) or int(which_episode) == 0:
                    self.entry.ep = int(which_episode)
                    if int(which_episode) != 0:
                        self.gen_eplink()
                    else:
                        self.entry.ep_url = None
                    break
                else:
                    error("Number out of range.")

            except:
                error("Invalid Input")

        return self.entry

    def pick_range(self):
        """
        Accept a range of episodes
        and return it.
        Input/output would be
        something like this:
             3-5 -> [3, 4, 5]
             3 -> [3]
        """
        self.entry.latest_ep = self.get_latest()
        while True:
            which_episode = input(
                self._create_prompt(prompt="Episode (Range with '-')")
            )

            which_episode = which_episode.split("-")

            if len(which_episode) == 1:
                try:
                    if self._validate_ep(which_episode[0]):
                        return which_episode
                except:
                    error("invalid input")
            elif len(which_episode) == 2:
                try:
                    ep_list = self._load_eps_list()

                    first_index = ep_list.index(
                        list(filter(lambda x: x["ep"] == which_episode[0], ep_list))[0]
                    )

                    second_index = ep_list.index(
                        list(filter(lambda x: x["ep"] == which_episode[1], ep_list))[0]
                    )

                    ep_list = ep_list[first_index : second_index + 1]

                    if not ep_list:
                        error("invlid input1")
                    else:
                        return [x["ep"] for x in ep_list]

                except Exception as e:
                    error(f"invalid input {e}")
            else:
                error("invalid input")

    def next_ep(self):
        """
        Increment ep and return the entry.
        """
        self.get_latest()
        if self.entry.ep == self.entry.latest_ep:
            error("no more episodes")
            return self.entry
        else:
            self.entry.ep += 1
            self.gen_eplink()
            return self.entry

    def prev_ep(self):
        """
        Decrement ep and return the entry.
        """
        if self.entry.ep == 1:
            error("no more episodes")
            return self.entry
        else:
            self.entry.ep -= 1
            self.gen_eplink()
            return self.entry


class videourl:
    """
    Class that fetches embed and
    stream url.
    """

    def __init__(self, entry, quality) -> None:
        self.entry = entry
        self.qual = quality.lower().strip("p")
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.ajax_url = "/encrypt-ajax.php?"
        self.enc_key_api = "https://raw.githubusercontent.com/justfoolingaround/animdl-provider-benchmarks/master/api/gogoanime.json"
        self.mode = AES.MODE_CBC
        self.size = AES.block_size
        self.padder = "\x08\x0e\x03\x08\t\x03\x04\t"
        self.pad = lambda s: s + chr(len(s) % 16) * (16 - len(s) % 16)
        keys = self.get_encryption_keys()
        self.iv = keys["iv"]
        self.key = keys["key"]
        self.second_key = keys["second_key"]

    def get_entry(self):
        """
        Returns the entry with stream and emebed url fields filled
        which was previously passed to this class.
        """
        return self.entry

    def embed_url(self):
        r = self.session.get(self.entry.ep_url)
        response_err(r, self.entry.ep_url)
        soup = BeautifulSoup(r.content, "html.parser")
        link = soup.find("a", {"class": "active", "rel": "1"})
        loc_err(link, self.entry.ep_url, "embed-url")
        self.entry.embed_url = f'https:{link["data-video"]}'

    @functools.lru_cache()
    def get_encryption_keys(self):
        return {
            _: __.encode()
            for _, __ in self.session.get(self.enc_key_api).json().items()
        }

    def aes_encrypt(self, data, key):
        return base64.b64encode(
            AES.new(key, self.mode, iv=self.iv).encrypt(self.pad(data).encode())
        )

    def aes_decrypt(self, data, key):
        return (
            AES.new(key, self.mode, iv=self.iv)
            .decrypt(base64.b64decode(data))
            .strip(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\x0c\r\x0e\x0f\x10")
        )

    def get_data(self):
        r = self.session.get(self.entry.embed_url)
        soup = BeautifulSoup(r.content, "html.parser")
        crypto = soup.find("script", {"data-name": "episode"})
        loc_err(crypto, self.entry.embed_url, "token")
        return crypto["data-value"]

    def stream_url(self):
        """
        Fetches stream url and executes
        quality function.
        """
        if not self.entry.embed_url:
            self.embed_url()

        parsed = urlparse(self.entry.embed_url)
        self.ajax_url = parsed.scheme + "://" + parsed.netloc + self.ajax_url

        data = self.aes_decrypt(self.get_data(), self.key).decode()
        data = dict(parse_qsl(data))

        id = urlparse(self.entry.embed_url).query
        id = dict(parse_qsl(id))["id"]
        enc_id = self.aes_encrypt(id, self.key).decode()
        data.update(id=enc_id)

        headers = {
            "x-requested-with": "XMLHttpRequest",
            "referer": self.entry.embed_url,
        }

        r = self.session.post(
            self.ajax_url + urlencode(data) + f"&alias={id}",
            headers=headers,
        )

        response_err(r, r.url)

        json_resp = json.loads(self.aes_decrypt(r.json().get("data"), self.second_key))

        source_data = [x for x in json_resp["source"]]
        self.quality(source_data)

    def quality(self, json_data):
        """
        Get quality options from
        JSON repons and change
        stream url to the either
        the quality option that was picked,
        or the best one avalible.
        """
        self.entry.quality = ""

        streams = []
        for i in json_data:
            if "m3u8" in i["file"] or i["type"] == "hls":
                type = "hls"
            else:
                type = "mp4"

            quality = i["label"].replace(" P", "").lower()

            streams.append({"file": i["file"], "type": type, "quality": quality})

        # if len(streams) == 1:
        #    streams = extract_m3u8_streams(
        #        streams[0]['file']
        #    )

        filtered_q_user = list(filter(lambda x: x["quality"] == self.qual, streams))

        if filtered_q_user:
            stream = list(filtered_q_user)[0]
        elif self.qual == "best" or self.qual == None:
            stream = streams[-1]
        elif self.qual == "worst":
            stream = streams[0]
        else:
            error("quality not avalible, using default")
            stream = streams[-1]

        self.entry.quality = stream["quality"]
        self.entry.stream_url = stream["file"]


def extract_m3u8_streams(uri):
    if re.match(r"https?://", uri):
        resp = requests.get(uri)
        resp.raise_for_status()
        raw_content = resp.content.decode(resp.encoding or "utf-8")
        base_uri = urljoin(uri, ".")
    else:
        with open(uri) as fin:
            raw_content = fin.read()
            base_uri = Path(uri)

    content = m3u8.M3U8(raw_content, base_uri=base_uri)
    content.playlists.sort(key=lambda x: x.stream_info.bandwidth)
    streams = []
    for playlist in content.playlists:
        streams.append(
            {
                "file": urljoin(content.base_uri, playlist.uri),
                "type": "hls",
                "quality": str(playlist.stream_info.resolution[1]),
            }
        )

    return streams
