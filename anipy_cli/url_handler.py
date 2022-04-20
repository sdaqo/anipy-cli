import sys
import json
import requests
import re
import base64
import functools
from urllib.parse import urlparse, parse_qsl, urlencode
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter, Retry
from Cryptodome.Cipher import AES

from .misc import response_err, error, loc_err
from .colors import colors


class epHandler:
    """
    Class for handling episodes and stuff.
    Requires at least the category_url field of the
    entry to be filled.
    """

    def __init__(self, entry) -> None:
        self.entry = entry

    def get_entry(self):
        """
        Returns the entry with which was
        previously passed to this class.
        """
        return self.entry

    def get_latest(self):
        """
        Fetch latest episode avalible
        from a show and return it.
        """
        r = requests.get(self.entry.category_url)
        response_err(r, self.entry.category_url)
        soup = BeautifulSoup(r.content, "html.parser")
        ep_count = [
            i.get("ep_end")
            for i in soup.find_all("a", attrs={"ep_end": re.compile(r"^ *\d[\d ]*$")})
        ]

        if not ep_count:
            error("could not get latest episode")
            sys.exit()

        self.entry.latest_ep = int(ep_count[-1])

        return self.entry.latest_ep

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

    def pick_ep(self):
        """
        Cli function to pick a episode from 1 to
        the latest avalible.
        """

        self.get_latest()

        while True:
            which_episode = input(
                colors.END
                + "Episode "
                + colors.GREEN
                + f"[1-{self.entry.latest_ep}]"
                + colors.END
                + ": "
                + colors.CYAN
            )
            try:
                if int(which_episode) in list(range(1, self.entry.latest_ep + 1)):
                    self.entry.ep = int(which_episode)
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
                colors.END
                + "Last Episode you watched (put 0 to start at the beginning) "
                + colors.GREEN
                + f"[0-{self.entry.latest_ep}]"
                + colors.END
                + ": \n>> "
                + colors.CYAN
            )
            try:
                if int(which_episode) in list(range(0, self.entry.latest_ep + 1)):
                    self.entry.ep = int(which_episode)
                    self.gen_eplink()
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
                colors.END
                + "Episode "
                + colors.GREEN
                + f"[1-{self.entry.latest_ep}]"
                + colors.END
                + ": "
                + colors.CYAN
            )

            which_episode = which_episode.split("-")

            if len(which_episode) == 1:
                try:
                    if int(which_episode[0]) in list(
                        range(1, self.entry.latest_ep + 1)
                    ):
                        return which_episode
                except:
                    error("invalid input")
            elif len(which_episode) == 2:
                try:
                    ep_list = list(
                        range(int(which_episode[0]), int(which_episode[1]) + 1)
                    )
                    if not ep_list:
                        error("invlid input")
                    else:
                        if ep_list[-1] > self.entry.latest_ep:
                            error("invalid input")
                        else:
                            return ep_list
                except:
                    error("invalid input")
            else:
                error("invalid input")

    def gen_eplink(self):
        """
        Generate episode url
        from ep and category url
        will look something like this:
        https://gogoanime.film/category/hyouka
        to
        https://gogoanime.film/hyouka-episode-1
        """
        self.entry.ep_url = self.entry.category_url.replace("/category", "")
        self.entry.ep_url = self.entry.ep_url + f"-episode-{self.entry.ep}"

        return self.entry


class videourl:
    """
    Class that fetches embed and
    stream url.
    """

    def __init__(self, entry, quality) -> None:
        self.entry = entry
        self.qual = quality
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
        if "fc24fc6eef71638a72a9b19699526dcb" in json_data[0]["file"]:
            r = self.session.get(
                json_data[0]["file"], headers={"referer": self.entry.embed_url}
            )

            qualitys = re.findall(r"(?<=\d\d\dx)\d+", r.text)
            quality_links = [x for x in r.text.split("\n")]
            quality_links = [x for x in quality_links if not x.startswith("#")]
            if "fc24fc6eef71638a72a9b19699526dcb" in json_data[0]["file"]:
                qualitys.reverse()
                quality_links.reverse()

            quality_links = list(filter(None, quality_links))

        else:
            qualitys = []
            quality_links = []
            for i in json_data:
                if i["label"] == "Auto":
                    pass
                else:
                    qualitys.append(i["label"])
                    quality_links.append(i["file"])

            qualitys = [x.replace(" P", "") for x in qualitys]

        if self.qual in qualitys:
            q = quality_links[qualitys.index(self.qual)]
        elif self.qual == "best" or self.qual == None:
            q = quality_links[-1]
        elif self.qual == "worst":
            q = quality_links[0]
        else:
            error("quality not avalible, using default")
            q = quality_links[-1]

        if "fc24fc6eef71638a72a9b19699526dcb.com" in json_data[0]["file"]:
            self.entry.stream_url = json_data[0]["file"].rsplit("/", 1)[0] + "/" + q
        else:
            self.entry.stream_url = q

        chosen_quality = q.split("/")

        for _qual in chosen_quality:

            if "EP" in _qual:
                self.entry.quality = _qual.split(".")[4]

        if not self.entry.quality:
            self.entry.quality = str(qualitys[quality_links.index(q)] + "p")
