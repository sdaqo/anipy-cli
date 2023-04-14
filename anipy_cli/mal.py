import base64
import datetime
import json
import os
import sys
import time
from copy import deepcopy
from multiprocessing import Pool

import requests
from requests.adapters import HTTPAdapter, Retry

from anipy_cli.url_handler import epHandler
from anipy_cli.seasonal import Seasonal
from anipy_cli.query import query
from anipy_cli.colors import colors, cprint
from anipy_cli.config import Config
from anipy_cli.misc import read_json, error, Entry


def _base64_decode(b64: str):
    return base64.b64decode(b64).decode("ascii")


def _base64_encode(string: str):
    message_bytes = string.encode("ascii")
    return base64.b64encode(message_bytes).decode("ascii")


class MAL:
    """
    MyAnimeList API client
    """

    def __init__(self, user=None, password=None):
        # API information taken from here: https://github.com/SuperMarcus/myanimelist-api-specification
        self.entry = Entry()
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
        self.mal_user = (
            Config().mal_user
            if Config().mal_user and Config().mal_user != ""
            else (user if user else False)
        )
        self.mal_password = (
            password
            if password
            else (
                Config().mal_password
                if Config().mal_password and Config().mal_password != ""
                else False
            )
        )
        self.anime_list = None
        self.gogo_baseurl = Config().gogoanime_url
        self.data = {
            "client_id": self.api_client_id,
        }
        self.shows_failed_automap = set()

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
        if self.mal_user:
            if not self.auth():
                error(
                    "Could not authenticate with MyAnimeList. Please check your credentials..."
                )
            self.get_anime_list()
            if Config().auto_map_mal_to_gogo:
                self.auto_map_all_without_map()
            if Config().auto_sync_mal_to_seasonals:
                self.sync_mal_with_seasonal()

    def auto_map_all_without_map(self):
        with Pool(processes=None) as pool:
            mal_entries = self.local_mal_list_json["data"]
                # apply the search function to each search value in parallel
            results = pool.map(self.auto_map_gogo_mal, mal_entries, True)


        new_mal_entries = list()
        for result in results:
            if type(result) is dict:
                new_mal_entries.append(result["mal_entry"])
                if result["failed_to_map"] is True:
                    self.shows_failed_automap.add(result["mal_entry"]["node"]["title"])
                else:
                    self.shows_failed_automap.discard(
                        result["mal_entry"]["node"]["title"]
                    )
        self.local_mal_list_json["data"] = new_mal_entries
        self.write_save_data()

        return self.shows_failed_automap

    def get_all_without_gogo_map(self):
        shows_with_no_map = set()
        for mal_entry in self.local_mal_list_json["data"]:
            if "gogo_map" not in mal_entry or len(mal_entry["gogo_map"]) < 1:
                shows_with_no_map.add(mal_entry["node"]["title"])
        return shows_with_no_map

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

            if "message" in request_error.response.json():
                error(
                    "MyAnimeList Error: {}".format(
                        request_error.response.json()["message"]
                    )
                )
                if "hint" in request_error.response.json():
                    print(
                        "{}Hint:{} {}{}".format(
                            colors.BLUE,
                            colors.YELLOW,
                            request_error.response.json()["hint"],
                            colors.END,
                        )
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
            print("MAL: Auth with user and password")
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

        url = f"{self.api_baseurl}users/@me/animelist"
        anime_list = self.get_all_anime_pages(
            url, limit=20, additional_params=parameters
        )
        if not isinstance(anime_list, dict):
            return False
        if not isinstance(anime_list, requests.exceptions.RequestException):
            self.anime_list = deepcopy(anime_list)
            self.write_mal_list()
            return anime_list["data"]

        else:
            return None

    def update_anime_list(self, anime_id: int, update_data: dict = None):
        url = f"{self.api_baseurl}anime/{anime_id}/my_list_status"
        allowed_update_data_keys = ["status", "num_watched_episodes", "tags"]
        data = {}
        for key, value in update_data.items():
            if key in allowed_update_data_keys:
                data[key] = value
        if data:
            self._make_request(url, "patch", data)

    def get_seasonal_anime(
        self, year: int, season: str, limit: int = 100, automap: bool = False
    ):
        season = season.lower()
        url = f"{self.api_baseurl}anime/season/{year}/{season}"

        anime_season_list = self.get_all_anime_pages(url, limit)["data"]

        return anime_season_list

    def get_anime(self, query: str, limit: int = 2, automap: bool = True):
        url = f"{self.api_baseurl}anime"
        params = {
            "q": query,
            "limit": 10,
        }
        anime_found = self._make_request(url, "get", query_params=params)
        if (
            isinstance(anime_found, requests.exceptions.RequestException)
            or not isinstance(anime_found, dict)
            or len(anime_found["data"]) < 1
        ):
            return []

        return anime_found["data"]

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
        anime_list = {"data": []}

        while next_page:
            response = self._make_request(url, "get", query_params=params)
            if not "data" in response or not isinstance(response["data"], list):
                continue
            if (
                response["paging"]
                and "next" in response["paging"]
                and response["paging"]["next"]
            ):
                offset += limit

            else:
                next_page = False

            anime_list["data"] += response["data"]
            params["offset"] = offset

            # sleep for 0.5 sec to limit rate
            time.sleep(0.5)
        return anime_list

    def add_show(self, show_name, category_url, picked_ep):
        search = self.get_anime(show_name, automap=True)

        if isinstance(search, requests.exceptions.RequestException):
            return None

        else:
            if search[0]["node"]["title"].lower() == show_name.lower().rstrip(
                " (dub)"
            ).strip("(japanese dub)"):
                print("Exact match")
                self.update_anime_list(
                    search[0]["node"]["id"],
                    {
                        "status": "watching",
                        "num_watched_episodes": picked_ep,
                        "tags": "anipy-cli",
                    },
                )
                show = [
                    x
                    for x in self.local_mal_list_json["data"]
                    if x["node"]["title"] == search[0]["node"]["title"]
                ]
                try:
                    new_item = self.make_gogo_map(category_url, show_name)
                    if "gogo_map" in show[0]:
                        self.update_gogo_map_list(show[0]["gogo_map"], new_item)

                    else:
                        new_map = {"gogo_map": []}
                        self.update_gogo_map_list(new_map["gogo_map"], new_item)
                        show[0].update(new_map)
                except IndexError:
                    error("No show found for {}".format(search[0]["node"]["title"]))

                self.write_mal_list()
            else:
                return search

    def make_gogo_map(self, link_href, name):
        link = (
            link_href
            if len(link_href.split("/category/")[0]) > 3
            else Config().gogoanime_url + link_href
        )
        if "(dub)" in name.lower():
            key = "dub"

        else:
            key = "sub"

        return [{"name": name, "link": link, "type": key}]

    def update_gogo_map_list(self, gogo_map, new_entry):
        if len(gogo_map) > 0:
            for index, item in enumerate(gogo_map):
                if item["name"] == new_entry[0]["name"]:
                    if item.__eq__(new_entry):
                        return True

                    else:
                        gogo_map[index] = new_entry
                        return True
        if isinstance(gogo_map, list):
            gogo_map.extend(new_entry)

        return True

    def read_save_data(self):
        try:
            self.local_mal_list_json = read_json(Config().mal_local_user_list_path)

        except json.decoder.JSONDecodeError:
            pass

        if (
            not isinstance(self.local_mal_list_json, dict)
            or "data" not in self.local_mal_list_json
        ):
            self.local_mal_list_json = {"data": []}
            self.get_anime_list(automap=True)

    def write_save_data(self):
        try:
            with Config().mal_local_user_list_path.open("w") as f:
                json.dump(self.local_mal_list_json, f, indent=4)

        except PermissionError:
            error("Unable to write to local MAL-list file due permissions.")
            sys.exit()

    def write_mal_list(self):
        for show_entry in self.anime_list["data"]:
            if "data" not in self.local_mal_list_json:
                self.local_mal_list_json = {"data": []}
            show = [
                x
                for x in self.local_mal_list_json["data"]
                if x["node"]["title"] == show_entry["node"]["title"]
            ]
            if len(show) > 0:
                update_dict_recursive(show[0]["node"], show_entry["node"])

            else:
                self.local_mal_list_json["data"].append(show_entry)

        self.write_save_data()

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
        self.delete_mal_entry(anime_id)

        pass

    def latest_eps(self, all_eps: bool = False):
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
        entries = [
            i
            for i in self.local_mal_list_json["data"]
            if i["node"]["my_list_status"]["status"] in Config().mal_status_categories
        ]

        latest_urls = {}
        for i in entries:
            if all_eps:
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

            for key, link in enumerate(i["gogo_map"]):
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
        show = []
        for mal_entry in self.local_mal_list_json["data"]:
            if "gogo_map" in mal_entry.keys():
                for gogomap in mal_entry["gogo_map"]:
                    if gogo_show_name in gogomap["name"]:
                        show.append(mal_entry)
                        break
        if len(show) > 0:
            anime_id = show[0]["node"]["id"]
            self.update_anime_list(anime_id, {"num_watched_episodes": ep})

    def sync_mal_with_seasonal(self):
        self.get_anime_list()
        seasonal = Seasonal()
        seasonal_list = seasonal.list_seasonals()
        for mal_with_gogo_map in self.local_mal_list_json["data"]:
            if (
                mal_with_gogo_map["node"]["my_list_status"]["status"]
                in Config().mal_status_categories
                and "gogo_map" in mal_with_gogo_map
                and len(mal_with_gogo_map["gogo_map"]) > 0
            ):
                for anime_entry in mal_with_gogo_map["gogo_map"]:
                    print(
                        "{}Syncing {}{}".format(
                            colors.GREEN, anime_entry["name"], colors.END
                        )
                    )
                    if anime_entry["name"] in [x[0] for x in seasonal_list]:
                        seasonal.update_show(
                            anime_entry["name"],
                            anime_entry["link"],
                            mal_with_gogo_map["node"]["my_list_status"][
                                "num_episodes_watched"
                            ],
                        )

                    else:
                        seasonal.add_show(
                            anime_entry["name"],
                            anime_entry["link"],
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

    def auto_map_gogo_mal(self, mal_entry, mp=False):
        # Look issue 122
        try:
            if "gogo_map" in mal_entry and len(mal_entry["gogo_map"]) > 0:
                return {"failed_to_map": False, "mal_entry": mal_entry}
            failed_to_map = True
            cprint(colors.GREEN, "Auto mapping: ", colors.BLUE, mal_entry["node"]["title"])

            search_values = [
                mal_entry["node"]["title"],
                mal_entry["node"]["alternative_titles"]["en"],
            ] + mal_entry["node"]["alternative_titles"]["synonyms"]

            found = {}
            for search in search_values:
                query_class = query(search, Entry)
                query_class.get_pages()
                found["search"] = query_class.get_links()

                if found["search"] == 0:
                    self.shows_failed_automap.add(mal_entry["node"]["title"])
                    continue
                if "gogo_map" not in mal_entry:
                    mal_entry["gogo_map"] = []
                for i, anime in enumerate(found["search"][1]):
                    if any(
                        anime.lower().rstrip("(dub)").rstrip("(japanese dub)").strip(" ")
                        in show.lower()
                        for show in [search_values[0], search_values[1]]
                    ):
                        gogo_map = mal_entry["gogo_map"]
                        current_map = self.make_gogo_map(found["search"][0][i], anime)

                        self.update_gogo_map_list(gogo_map, current_map)
                        failed_to_map = False
                        if not mp:
                            self.shows_failed_automap.discard(mal_entry["node"]["title"])
                        self.update_anime_list(
                            mal_entry["node"]["id"],
                            {
                                "num_watched_episodes": mal_entry["node"]["my_list_status"][
                                    "num_episodes_watched"
                                ],
                                "tags": "anipy-cli",
                            },
                        )
                    else:
                        if not mp:
                            self.shows_failed_automap.add(mal_entry["node"]["title"])
            if mp:
                self.write_save_data()
            return {"failed_to_map": failed_to_map, "mal_entry": mal_entry}
        except json.JSONDecodeError:
            return {"failed_to_map": True, "mal_entry": mal_entry}

    def manual_map_gogo_mal(self, mal_anime_name: str, gogo: dict):
        mal_entry = [
            x
            for x in self.local_mal_list_json["data"]
            if x["node"]["title"] == mal_anime_name
        ]
        if len(mal_entry) > 0:
            current_mal_entry = mal_entry[0]

        else:
            return False

        if "gogo_map" not in current_mal_entry or not isinstance(
            current_mal_entry["gogo_map"], list
        ):
            current_mal_entry["gogo_map"] = []

        self.update_gogo_map_list(
            current_mal_entry["gogo_map"],
            self.make_gogo_map(gogo["link"], gogo["name"]),
        )
        if mal_anime_name in self.shows_failed_automap:
            self.shows_failed_automap.discard(mal_anime_name)
        return True


def update_dict_recursive(dct, merge_dct):
    for k, v in merge_dct.items():
        if k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], dict):
            update_dict_recursive(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]
