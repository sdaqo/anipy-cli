from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Union

from dataclasses_json import config, DataClassJsonMixin

from anipy_cli.config import Config
from anipy_cli.provider import Episode
from anipy_cli.anime import Anime


@dataclass
class SeasonalEntry(DataClassJsonMixin):
    provider: str = field(metadata=config(field_name="pv"))
    identifier: str = field(metadata=config(field_name="id"))
    name: str = field(metadata=config(field_name="na"))
    episode: Episode = field(metadata=config(field_name="ep"))

    def __repr__(self) -> str:
        return f"{self.name} Episode {self.episode}"


@dataclass
class Seasonals(DataClassJsonMixin):
    seasonals: Dict[str, SeasonalEntry]

    def write(self):
        season_file = Config()._seasonal_file_path
        season_file.write_text(self.to_json())

    @staticmethod
    def read() -> "Seasonals":
        season_file = Config()._seasonal_file_path

        if not season_file.is_file():
            season_file.parent.mkdir(exist_ok=True, parents=True)
            return Seasonals({})

        try:
            seasonals: Seasonals = Seasonals.from_json(season_file.read_text())
        except KeyError:
            seasonals = _migrate_seasonals()

        return seasonals


def get_seasonals() -> Seasonals:
    return Seasonals.read()


def get_seasonal_entry(anime: "Anime") -> Optional[SeasonalEntry]:
    seasonals = Seasonals.read()
    uniqueid = f"{anime.provider.NAME}:{anime.identifier}"

    return seasonals.seasonals.get(uniqueid, None)


def delete_seasonal(anime: Union["Anime", SeasonalEntry]):
    seasonals = Seasonals.read()

    if isinstance(anime, Anime):
        uniqueid = f"{anime.provider.NAME}:{anime.identifier}"
    else:
        uniqueid = f"{anime.provider}:{anime.identifier}"

    seasonals.seasonals.pop(uniqueid)
    seasonals.write()


def update_seasonal(anime: Union["Anime", SeasonalEntry], episode: "Episode"):
    seasonals = Seasonals.read()

    if isinstance(anime, Anime):
        provider = anime.provider.NAME
        identifier = anime.identifier
    else:
        provider = anime.provider
        identifier = anime.identifier

    uniqueid = f"{provider}:{identifier}"

    entry = seasonals.seasonals.get(uniqueid, None)

    if entry is None:
        entry = SeasonalEntry(
            provider=provider,
            identifier=identifier,
            name=anime.name,
            episode=episode,
        )
    else:
        entry.episode = episode

    seasonals.seasonals[uniqueid] = entry
    seasonals.write()


def _migrate_seasonals():
    import json

    season_file = Config()._seasonal_file_path
    old_data = json.load(season_file.open("r"))
    new_seasonals = Seasonals({})

    for k, v in old_data.items():
        name = k
        identifier = Path(v["category_url"]).name
        episode = v["ep"]
        unique_id = f"gogoanime:{identifier}"
        new_entry = SeasonalEntry(
            provider="gogoanmie", name=name, identifier=identifier, episode=episode
        )

        new_seasonals.seasonals[unique_id] = new_entry

    new_seasonals.write()
    return new_seasonals
