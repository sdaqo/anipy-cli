import base64
import datetime
import json
import os
import sys
import time
from copy import deepcopy

import bs4
import requests
from requests.adapters import HTTPAdapter, Retry

from . import epHandler, Seasonal
from .colors import colors
from .config import config
from .misc import read_json, error, entry


def _base64_decode(b64: str):
    return base64.b64decode(b64).decode("ascii")


def _base64_encode(string: str):
    message_bytes = string.encode("ascii")
    return base64.b64encode(message_bytes).decode("ascii")


class MAL:
    """
    MyAnimeList API client
    """

    def __init__(self):
        # API information taken from here: https://github.com/SuperMarcus/myanimelist-api-specification
        self.entry = entry()
        self.local_mal_list_json = None

        self.anime_fields = [
            "id",
            "title",
            "main_picture",
            "alternative_titles",
            "my_list_status{tags,is_rewatching,num_episodes_watched,score,status,updated_at}",
            "start_season",
        ]
        self.access_token_expire_time = None
        self.access_token = None
        self.refresh_token = os.environ.get("mal_api_refresh_token")
        self.api_client_id = "6114d00ca681b7701d1e15fe11a4987e"
        self.api_baseurl = "https://api.myanimelist.net/v2/"
        self.mal_user = config.mal_user if config.mal_user != "" else None
        self.mal_password = config.mal_password if config.mal_password != "" else None
        self.anime_list = None
        self.gogo_baseurl = config.gogoanime_url
        self.data = {
            "client_id": self.api_client_id,
        }

        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
            "X-MAL-Client-ID": self.api_client_id,
        }
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)
        self.read_save_data()
        if config.auto_sync_mal_to_seasonals:
            self.sync_mal_with_seasonal()

    def _make_request(
        self,
        url: str,
        method: str,
        data: dict = None,
        query_params: dict = None,
        body: dict = None,
        retry: int = 0,
        is_auth: bool = False,
    ):
        try:
            response = self.session.request(
                method, url, data=data, params=query_params, json=body
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as request_error:
            if retry == 0 and not is_auth:
                self.auth(retry=retry)
                return self._make_request(
                    url,
                    method,
                    data=data,
                    query_params=query_params,
                    body=body,
                    retry=1,
                )

            if (
                request_error.response.json()["message"]
                == "Incorrect username or password."
            ):
                error(
                    "Ivalid username or Password for MyAnimeList. Please check your config..."
                )
                sys.exit(1)
            error("MyAnimeList - {}".format(request_error.response.json()))
            return error

    def auth(self, retry: int = 0):
        data = self.data
        time_now = datetime.datetime.now()
        if (
            self.access_token
            and self.access_token_expire_time > time_now
            and retry == 0
        ):
            return True

        elif self.mal_user:
            print("MAL Auth with user and password")
            url = "https://api.myanimelist.net/v2/auth/token"
            data.update(
                {
                    "grant_type": "password",
                    "password": self.mal_password,
                    "username": self.mal_user,
                }
            )

        else:
            url = "https://myanimelist.net/v1/oauth2/token"
            data.update({"client_id": self.api_client_id})

        response = self._make_request(url, "post", data, is_auth=True)
        if isinstance(response, dict):
            if response["access_token"]:
                self.access_token = response["access_token"]
                self.session.headers.update(
                    {"Authorization": "Bearer " + self.access_token}
                )
                self.access_token_expire_time = time_now + datetime.timedelta(
                    0, int(response["expires_in"])
                )
                self.refresh_token = response["refresh_token"]
                os.environ["mal_api_refresh_token"] = self.refresh_token
                return True

            else:
                return None

        else:
            if retry == 0:
                return self.auth(retry=1)

            else:
                return None

    def get_anime_list(self, status_filter: str = None, automap: bool = False):
        if status_filter is not None:
            status_filter = status_filter.lower()

        allowed_filters = [
            "watching",
            "completed",
            "on_hold",
            "dropped",
            "plan_to_watch",
        ]
        parameters = {}
        if status_filter in allowed_filters:
            parameters = {"status": status_filter}

        parameters.update({"fields": ",".join(self.anime_fields)})
        url = f"{self.api_baseurl}users/@me/animelist"
        anime_list = self._make_request(
            url,
            "get",
            query_params=parameters,
        )
        if not isinstance(anime_list, dict):
            return False
        if not isinstance(anime_list, requests.exceptions.RequestException):
            if automap:
                self.add_automap_to_anime_list(anime_list["data"])

            self.anime_list = anime_list
            self.write_mal_list()
            return anime_list["data"]

        else:
            return None

    def get_anime_information(self, anime_id: int):
        url = f"{self.api_baseurl}anime/{anime_id}"
        anime_detail = self._make_request(url, "get")
        return anime_detail

    def update_anime_list(self, anime_id: int, update_data: dict = None):
        url = f"{self.api_baseurl}anime/{anime_id}/my_list_status"
        allowed_update_data_keys = ["status", "num_watched_episodes", "tags"]
        data = {}
        for key, value in update_data.items():
            if key in allowed_update_data_keys:
                data[key] = value
        if data:
            self._make_request(url, "patch", data)
            self.get_anime_list(automap=False)

    def get_seasonal_anime(
        self, year: int, season: str, limit: int = 100, automap: bool = False
    ):
        season = season.lower()
        url = f"{self.api_baseurl}anime/season/{year}/{season}"

        anime_season_list = self.get_all_anime_pages(url, limit)

        if automap:
            self.add_automap_to_anime_list(anime_season_list)

        return anime_season_list

    def get_anime(self, query: str, limit: int = 2, automap: bool = True):
        url = f"{self.api_baseurl}anime"
        params = {
            "q": query,
            "limit": 3,
        }
        anime_found = self._make_request(url, "get", query_params=params)

        if automap:
            self.add_automap_to_anime_list(anime_found)

        return anime_found

    def get_all_anime_pages(self, url, limit, additional_params: dict = None):
        params = {
            "fields": ",".join(self.anime_fields),
            "limit": limit,
            "offset": 0,
        }
        if additional_params:
            params.update(additional_params)
        next_page = True
        offset = 0
        anime_list = []
        while next_page:
            response = self._make_request(url, "get", query_params=params)
            if response["paging"]:
                offset += limit

            else:
                next_page = False

            anime_list.extend(response["data"])
            params["offset"] = offset

            # sleep for 0.5 sec to limit rate
            time.sleep(0.5)
        return anime_list

    def add_automap_to_anime_list(self, anime_list):
        for index, anime in enumerate(anime_list):
            start_year = ""
            if "start_season" in anime["node"]:
                start_year = anime["node"]["start_season"]["year"]
            gogo_map = self._automap_gogo_anime_urls(
                anime["node"]["title"], mal_release_year=start_year
            )
            if gogo_map:
                anime.update({"gogo_map": gogo_map})

    def _automap_gogo_anime_urls(
        self,
        anime_title: str,
        mal_release_year: str = "",
        dub: bool = False,
        sub: bool = True,
    ):
        dub = True if dub or "dub" in config.anime_types else False
        sub = True if sub or "sub" in config.anime_types else False

        gogo_anime_names_list = []
        gogo_anime_full_list = []
        if mal_release_year == "":
            mal_release_year = None

        gogo_anime_list = requests.get(
            f"{self.gogo_baseurl}search.html", params={"keyword": anime_title}
        )
        soup = bs4.BeautifulSoup(gogo_anime_list.content)
        anilist_list_items = soup.find("ul", attrs={"class": "items"}).findChildren(
            "li"
        )
        if not anilist_list_items:
            return None

        else:
            for link in anilist_list_items:
                released = link.find("p", attrs={"class": "released"})

                release_year = released.text
                if release_year == "":
                    release_year = None

                link_a = link.find("p", attrs={"class": "name"}).find("a")
                name = link_a.get("title")
                if not dub:
                    if "(dub)" in name.lower():
                        continue
                elif not sub:
                    if "(dub)" not in name.lower():
                        continue
                if (
                    release_year
                    and mal_release_year
                    and str(mal_release_year) not in release_year
                ):
                    continue

                gogo_anime_names_list.append(name)
                link_href = "{}{}".format(self.gogo_baseurl, link_a.get("href"))

                gogo_anime_full_list.append(self.make_gogo_map(link_href, name))

        if len(gogo_anime_full_list) == 0:
            return None

        return deepcopy(gogo_anime_full_list[0])

    def make_gogo_map(self, link_href, name):
        link_map = {}
        if "(dub)" in name.lower():
            key = "dub"
        else:
            key = "sub"
        link_map.update({key: {"name": name, "link": link_href}})
        return link_map

    def add_show(self, show_name, category_url, picked_ep):
        search = self.get_anime(show_name, automap=False)

        if isinstance(search, requests.exceptions.RequestException):
            return None

        else:
            if search["data"][0]["node"]["title"].lower() == show_name.lower().rstrip(
                " (dub)"
            ):
                print("Exact match")
                self.update_anime_list(
                    search["data"][0]["node"]["id"],
                    {
                        "status": "watching",
                        "num_watched_episodes": picked_ep,
                        "tags": "anipy-cli",
                    },
                )
                show = [
                    x
                    for x in self.local_mal_list_json["data"]
                    if x["node"]["title"] == search["data"][0]["node"]["title"]
                ]
                if "gogo_map" in show[0]:
                    show[0]["gogo_map"].update(
                        self.make_gogo_map(category_url, show_name)
                    )

                else:
                    show[0].update(
                        {"gogo_map": self.make_gogo_map(category_url, show_name)}
                    )

                self.write_mal_list()
            else:
                return search["data"]

    def read_save_data(self):
        try:
            self.local_mal_list_json = read_json(config.mal_local_user_list_path)
        except json.decoder.JSONDecodeError:
            self.local_mal_list_json = {"data": []}
            self.get_anime_list(automap=True)

    def write_mal_list(self):
        for show_entry in self.anime_list["data"]:
            show = [
                x
                for x in self.local_mal_list_json["data"]
                if x["node"]["title"] == show_entry["node"]["title"]
            ]
            if len(show) > 0:
                show[0].update(show_entry)

            else:
                self.local_mal_list_json["data"].append(show_entry)
        without_gogo_map = [
            s for s in self.local_mal_list_json["data"] if "gogo_map" not in s
        ]
        if len(without_gogo_map) > 0:
            self.add_automap_to_anime_list(without_gogo_map)
        try:
            with config.mal_local_user_list_path.open("w") as f:
                json.dump(self.local_mal_list_json, f, indent=4)

        except PermissionError:
            error("Unable to write to local MAL-list file due permissions.")
            sys.exit()

    def delete_mal_entry(self, anime_id):
        show = [
            x
            for x in self.local_mal_list_json["data"]
            if str(x["node"]["id"]) == str(anime_id)
        ]
        show[0] = None
        self.get_anime_list()

    def del_show(self, anime_id):
        url = f"{self.api_baseurl}anime/{anime_id}/my_list_status"
        self._make_request(url, "delete")

        pass

    def latest_eps(self, all: bool = False):
        """
        returns a dict like so:
            {"name": {
                "ep_list": [[ep, ep-link], [], ...],
                "category_url": "https://"
                },
             "another anime": {
                 ...
                },
            }
        """

        self.read_save_data()
        entries = [i for i in self.local_mal_list_json["data"]]

        latest_urls = {}
        for i in entries:
            if all:
                start_ep = 0
            else:
                start_ep = i["node"]["my_list_status"]["num_episodes_watched"]

            if "gogo_map" not in i:

                error(
                    'MAL entry "{}" is missing gogo-map, please re-add to MAL...'.format(
                        i["node"]["title"]
                    )
                )
                continue

            for key, link in i["gogo_map"].items():
                self.entry.category_url = link["link"]
                ep_class = epHandler(self.entry)
                latest = ep_class.get_latest()
                eps_range = list(range(start_ep + 1, latest + 1))
                ep_urls = []
                for j in eps_range:
                    self.entry.ep = j
                    ep_class = epHandler(self.entry)
                    entry = ep_class.gen_eplink()
                    ep_urls.append([j, entry.ep_url])

                latest_urls.update(
                    {
                        link["name"]: {
                            "ep_list": ep_urls,
                            "category_url": self.entry.category_url,
                        }
                    }
                )

        return latest_urls

    def update_watched(self, gogo_show_name, ep):
        show = [
            x
            for x in self.local_mal_list_json["data"]
            if gogo_show_name in x["gogo_map"].items()["name"]
        ]
        if len(show) > 0:
            anime_id = show[0]["node"]["id"]
            self.update_anime_list(anime_id, {"num_watched_episodes": ep})

    def sync_mal_with_seasonal(self):
        self.get_anime_list()
        seasonal = Seasonal()
        seasonal_list = seasonal.list_seasonals()
        for mal_with_gogo_map in self.local_mal_list_json["data"]:
            if (
                "gogo_map" in mal_with_gogo_map
                and len(mal_with_gogo_map["gogo_map"].items()) > 0
            ):
                for anime_type, link in mal_with_gogo_map["gogo_map"].items():
                    if link["name"] in [x[0] for x in seasonal_list]:
                        seasonal.update_show(
                            link["name"],
                            link["link"],
                            mal_with_gogo_map["node"]["my_list_status"][
                                "num_episodes_watched"
                            ],
                        )

                    else:
                        seasonal.add_show(
                            link["name"],
                            link["link"],
                            mal_with_gogo_map["node"]["my_list_status"][
                                "num_episodes_watched"
                            ],
                        )

    def sync_seasonals_with_mal(self):
        seasonal = Seasonal()
        seasonal_list = seasonal.export_seasonals()
        for anime in seasonal_list:
            print(f"{colors.GREEN}Syncing {anime[0]} into MAL{colors.END} ...")
            self.add_show(anime[0], anime[1], anime[2])
            print(f"{colors.GREEN}Done.{colors.END}")
