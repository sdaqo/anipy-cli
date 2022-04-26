import datetime
import os
import time
from pprint import pprint

import requests
from requests.adapters import HTTPAdapter, Retry
import urllib
from config import config


class MAL:
    """
    MyAnimeList API client
    """

    def __init__(self):
        # API information taken from here: https://github.com/SuperMarcus/myanimelist-api-specification
        self.anime_fields = [
            "id",
            "title",
            "main_picture",
            "alternative_titles",
            "my_list_status",
        ]
        self.access_token_expire_time = None
        self.access_token = None
        self.refresh_token = os.environ.get('mal_api_refresh_token')
        self.api_client_id = "6114d00ca681b7701d1e15fe11a4987e"
        self.api_baseurl = "https://api.myanimelist.net/v2/"
        self.mal_user = config.mal_user if config.mal_user == "" else None
        self.mal_password = config.mal_password if config.mal_password == "" else None
        self.anime_list = None
        self.data = {
            "client_id": self.api_client_id,
        }

        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36",
            "X-MAL-Client-ID": self.api_client_id
        }
        self.session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        self.session.headers.update(self.headers)

    def _make_request(self, url: str, method: str, data: dict = None, query_params: dict = None, body: dict = None,
                      retry: int = 0, is_auth: bool = False):
        try:
            response = self.session.request(method, url, data=data, params=query_params, json=body)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as error:
            if retry == 0 and not is_auth:
                self.auth(retry=retry)
                return self._make_request(url, method, data=data, query_params=query_params, body=body, retry=1)

            print("MyAnimeList Error: {}".format(error.response.json()))
            return error

    def auth(self, retry: int = 0):
        data = self.data
        time_now = datetime.datetime.now()
        if retry == 0 and self.refresh_token:
            if self.access_token and self.access_token_expire_time > time_now:
                return True

            url = "https://myanimelist.net/v1/oauth2/token"
            data.update(
                {
                    "grant_type": "refresh_token",
                    "refresh_token": self.refresh_token
                }
            )

        elif self.mal_user:
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
            data.update(
                {
                    "client_id": self.api_client_id
                }
            )

        response = self._make_request(url, "post", data, is_auth=True)
        if isinstance(response, dict):
            if response['access_token']:
                self.access_token = response['access_token']
                self.session.headers.update({"Authorization": "Bearer " + self.access_token})
                self.access_token_expire_time = time_now + datetime.timedelta(0, int(response['expires_in']))
                self.refresh_token = response['refresh_token']
                os.environ['mal_api_refresh_token'] = self.refresh_token
                print("Refresh Token after auth call: {}".format(self.refresh_token))
                print(str(response))
                return True

            else:
                return None

        else:
            if retry == 0:
                return self.auth(retry=1)

            else:
                return None

    def get_anime_list(self, status_filter: str = None):
        parameters = None
        if status_filter is not None:
            status_filter = status_filter.lower()

        allowed_filters = [
            "watching",
            "completed",
            "on_hold",
            "dropped",
            "plan_to_watch",

        ]
        if status_filter in allowed_filters:
            parameters = {"status": status_filter}

        parameters.update({"fields": ",".join(self.anime_fields)})
        url = f"{self.api_baseurl}users/@me/animelist"
        anime_list = self._make_request(url, "get", query_params=parameters, )
        pprint(anime_list)
        if isinstance(anime_list, dict):
            self.anime_list = anime_list['data'][0]
            return anime_list['data']

        else:
            return None

    def get_anime_information(self, anime_id: int):
        url = f"{self.api_baseurl}anime/{anime_id}"
        anime_detail = self._make_request(url, "get")
        pprint(anime_detail)
        return anime_detail

    def update_anime_list(self, anime_id: int, update_data: dict = None):
        url = f"{self.api_baseurl}anime/{anime_id}/my_list_status"
        allowed_update_data_keys = [
            "status",
            "num_watched_episodes",
        ]
        data = {}
        for key, value in update_data.items():
            if key in allowed_update_data_keys:
                data[key] = value
        if data:
            self._make_request(url, "patch", data)

    def get_seasonal_anime(self, year: int, season: str, limit: int = 100):
        season = season.lower()
        url = f"{self.api_baseurl}anime/season/{year}/{season}"
        params = {
            "fields": ",".join(self.anime_fields),
            "limit": limit,
        }
        next_page = True
        offset = 0
        anime_season_list = []
        while next_page:
            response = self._make_request(url, "get", query_params=params)
            if response["paging"]:
                offset += limit

            else:
                next_page = False

            anime_season_list.extend(response['data'])

            # sleep for 0.5 sec to limit rate
            time.sleep(.5)

        pprint(anime_season_list)



mal = MAL()
#mal.auth()
my_anime_list = mal.get_anime_list(status_filter="watching")
#mal.update_anime_list(my_anime_list[0]["node"]["id"], {"status": "watching", "num_watched_episodes": 4})
mal.get_seasonal_anime(2022, "spring", 200)
