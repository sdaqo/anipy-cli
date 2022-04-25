import json
import sys

from . import config
from .url_handler import epHandler
from .misc import entry, error, read_json


class Seasonal:
    def __init__(self):
        self.entry = entry()

    def latest_eps(self):
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
        names = [i for i in self.json]
        categ_urls = []
        user_eps = []
        for i in names:
            categ_urls.append(self.json[i]["category_url"])
            user_eps.append(self.json[i]["ep"])

        latest_urls = {}
        for i, e, n in zip(categ_urls, user_eps, names):
            self.entry.category_url = i
            ep_class = epHandler(self.entry)
            latest = ep_class.get_latest()
            eps_range = list(range(e + 1, latest + 1))
            ep_urls = []
            for j in eps_range:
                self.entry.ep = j
                ep_class = epHandler(self.entry)
                entry = ep_class.gen_eplink()
                ep_urls.append([j, entry.ep_url])

            latest_urls.update({n: {"ep_list": ep_urls, "category_url": i}})

        return latest_urls

    def read_save_data(self):
        self.json = read_json(config.seasonal_file_path)

    def write_seasonals(self):
        try:
            with config.seasonal_file_path.open("w") as f:
                json.dump(self.json, f)

        except PermissionError:
            error("Unable to write to history file due permissions.")
            sys.exit()

    def update_show(self, name, categ_url):
        self.read_save_data()

        if name not in [x for x in self.json]:
            return 0

        self.entry.category_url = categ_url
        self.json[name]["ep"] = epHandler(self.entry).get_latest()
        self.write_seasonals()

    def add_show(self, name, categ_url, start_ep):
        self.read_save_data()

        if name in [x for x in self.json]:
            return 0

        dic = {name: {"ep": start_ep, "category_url": categ_url}}

        self.json.update(dic)
        self.write_seasonals()

    def del_show(self, name):
        self.read_save_data()

        if name not in [x for x in self.json]:
            return 0

        self.json.pop(name)
        self.write_seasonals()

    def list_seasonals(self):
        self.read_save_data()

        return [[i, self.json[i]["ep"]] for i in self.json]
