import json
import sys

from anipy_cli.config import Config
from anipy_cli.url_handler import epHandler
from anipy_cli.misc import Entry, error, read_json
from anipy_cli.misc import parsenum


class Seasonal:
    def __init__(self):
        self.entry = Entry()

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
            
            eps_range = ep_class._load_eps_list()
            for j in eps_range:
                if parsenum(j["ep"]) == e:
                    eps_range = eps_range[eps_range.index(j) + 1:]
                    break

            
            ep_urls = []
            for j in eps_range:
                self.entry.ep = parsenum(j["ep"])
                ep_class = epHandler(self.entry)
                entry = ep_class.gen_eplink()
                ep_urls.append([parsenum(j["ep"]), entry.ep_url])

            latest_urls.update({n: {"ep_list": ep_urls, "category_url": i}})

        return latest_urls

    def read_save_data(self):
        self.json = read_json(Config().seasonal_file_path)

    def write_seasonals(self):
        try:
            with Config().seasonal_file_path.open("w") as f:
                json.dump(self.json, f, indent=4)

        except PermissionError:
            error("Unable to write to history file due permissions.")
            sys.exit()

    def update_show(self, name, categ_url, ep=None):
        self.read_save_data()

        if name not in [x for x in self.json]:
            return 0

        self.entry.category_url = categ_url
        if ep is not None:
            self.json[name]["ep"] = ep

        else:
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

    def export_seasonals(self):
        self.read_save_data()
        return [
            [i, self.json[i]["category_url"], self.json[i]["ep"]] for i in self.json
        ]
