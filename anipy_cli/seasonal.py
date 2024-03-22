import json
from pathlib import Path
import sys

from anipy_cli.config import Config
from anipy_cli.url_handler import epHandler
from anipy_cli.misc import Entry, error, read_json
from anipy_cli.provider.utils import parsenum

from dataclasses import dataclass, field
from InquirerPy import inquirer
from time import time
from dataclasses_json import dataclass_json, config
from typing import Dict, Optional

from anipy_cli.config import Config
from anipy_cli.provider import Episode
from anipy_cli.anime import Anime

# TODO: History migration

@dataclass_json
@dataclass
class SeasonalEntry:
    provider: str = field(metadata=config(field_name="pv"))
    identifier: str = field(metadata=config(field_name="id"))
    name: str = field(metadata=config(field_name="na"))
    episode: Episode = field(metadata=config(field_name="ep"))


@dataclass_json
@dataclass
class Seasonals:
    seasonals: Dict[str, SeasonalEntry]

    def write(self):
        season_file = Config().seasonal_file_path
        season_file.write_text(self.to_json())

    
    @staticmethod
    def read() -> "Seasonals":
        season_file = Config().seasonal_file_path

        if not season_file.is_file():
            season_file.parent.mkdir(parents=True)
            return Seasonals({})
        
        try:
            seasonals: Seasonals = Seasonals.from_json(season_file.read_text())
        except KeyError:
            seasonals = _migrate_seasonals()

        return seasonals


def get_seasonal_entry(anime: Anime) -> Optional[SeasonalEntry]:
    seasonals = Seasonals.read()
    uniqueid = f"{anime.provider.NAME}:{anime.identifier}"

    return seasonals.seasonals.get(uniqueid, None)

def del_seasonal_entry(anime: Anime):
    seasonals = Seasonals.read()
    uniqueid = f"{anime.provider.NAME}:{anime.identifier}"

    seasonals.seasonals.pop(uniqueid)
    seasonals.write()


def update_seasonals(anime: Anime, episode: Episode):
    hist_file = Config().history_file_path
    seasonals = Seasonals.read()
    
    uniqueid = f"{anime.provider.NAME}:{anime.identifier}"
    entry = seasonals.seasonals.get(uniqueid, None)

    if entry is None:
        entry = SeasonalEntry(
            provider=anime.provider.NAME, 
            identifier=anime.identifier, 
            name=anime.name, 
            episode=episode, 
        )
    else:
        entry.episode = episode

    seasonals.seasonals[uniqueid] = entry
    seasonals.write() 

def _migrate_seasonals():
    import json

    season_file = Config().seasonal_file_path
    old_data = json.load(season_file.open("r"))
    new_seasonals = Seasonals({})

    for k, v in old_data.items():
        name = k
        identifier = Path(v['category_url']).name
        episode = v['ep']
        unique_id = f"gogoanime:{identifier}"
        new_entry = SeasonalEntry(
            provider="gogoanmie",
            name=name,
            identifier=identifier,
            episode=episode
        )

        new_seasonals.seasonals[unique_id] = new_entry

    new_seasonals.write()
    return new_seasonals

# class Seasonal:
#     def __init__(self):
#         self.entry = Entry()
#
#     def latest_eps(self):
#         """
#         returns a dict like so:
#             {"name": {
#                 "ep_list": [[ep, ep-link], [], ...],
#                 "category_url": "https://"
#                 },
#              "another anime": {
#                  ...
#                 },
#             }
#         """
#
#         self.read_save_data()
#         names = [i for i in self.json]
#         categ_urls = []
#         user_eps = []
#         for i in names:
#             categ_urls.append(self.json[i]["category_url"])
#             user_eps.append(self.json[i]["ep"])
#
#         latest_urls = {}
#         for i, e, n in zip(categ_urls, user_eps, names):
#             self.entry.category_url = i
#             ep_class = epHandler(self.entry)
#
#             eps_range = ep_class._load_eps_list()
#             for j in eps_range:
#                 if parsenum(j["ep"]) == e:
#                     eps_range = eps_range[eps_range.index(j) + 1 :]
#                     break
#
#             ep_urls = []
#             for j in eps_range:
#                 self.entry.ep = parsenum(j["ep"])
#                 ep_class = epHandler(self.entry)
#                 entry = ep_class.gen_eplink()
#                 ep_urls.append([parsenum(j["ep"]), entry.ep_url])
#
#             latest_urls.update({n: {"ep_list": ep_urls, "category_url": i}})
#
#         return latest_urls
    #
    # def export_seasonals(self):
    #     self.read_save_data()
    #     return [
    #         [i, self.json[i]["category_url"], self.json[i]["ep"]] for i in self.json
    #     ]
