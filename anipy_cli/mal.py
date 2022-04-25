import datetime
import os

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
        self.access_token_expire_time = None
        self.access_token = None
        self.refresh_token = os.environ.get('mal_api_refresh_token')
        self.api_client_id = "6114d00ca681b7701d1e15fe11a4987e"
        self.api_baseurl = "https://api.myanimelist.net/v2/"
        self.mal_user = None
        self.mal_password = None
        self.data = {
            "client_id": self.api_client_id,
        }
        if (
                isinstance(config.mal_user, str) and
                isinstance(config.mal_password, str) and
                config.mal_user != "" and
                config.mal_password != ""
        ):
            self.mal_user = config.mal_user
            self.mal_password = config.mal_password

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

    def _make_request(self, url, method, data=None, query_params=None, body=None, retry=0):
        try:
            response = self.session.request(method, url, data=data, params=query_params, json=body)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as error:
            if retry == 0:
                self.auth()
                return self._make_request(url, method, data=data, query_params=query_params, body=body, retry=1)
            print("MyAnimeList Error: {}".format(error.response.json()))
            return error

    def auth(self, retry=0):
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

        response = self._make_request(url, "post", data)
        if isinstance(response, dict):
            if response['access_token']:
                self.access_token = response['access_token']
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


mal = MAL()
mal.auth()
