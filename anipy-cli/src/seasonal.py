from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Union

from dataclasses_json import DataClassJsonMixin, config

from anipy_cli.anime import Anime
from anipy_cli.config import Config
from anipy_cli.provider import Episode


@dataclass
class SeasonalEntry(DataClassJsonMixin):
    provider: str = field(metadata=config(field_name="pv"))
    identifier: str = field(metadata=config(field_name="id"))
    name: str = field(metadata=config(field_name="na"))
    episode: Episode = field(metadata=config(field_name="ep"))
    dub: bool = field(metadata=config(field_name="d"))
    has_dub: bool = field(metadata=config(field_name="hd"))

    def __repr__(self) -> str:
        return f"{self.name} ({'dub' if self.dub else 'sub'}) Episode {self.episode}"

    def __hash__(self) -> int:
        return hash(_get_uid(self, self.dub))


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


def get_seasonal_entry(anime: "Anime", dub: bool) -> Optional[SeasonalEntry]:
    seasonals = Seasonals.read()

    return seasonals.seasonals.get(_get_uid(anime, dub), None)


def delete_seasonal(anime: Union["Anime", SeasonalEntry], dub: bool):
    seasonals = Seasonals.read()

    seasonals.seasonals.pop(_get_uid(anime, dub))
    seasonals.write()


def update_seasonal(
    anime: Union["Anime", SeasonalEntry], episode: "Episode", dub: bool
):
    seasonals = Seasonals.read()

    if isinstance(anime, Anime):
        provider = anime.provider.NAME
        identifier = anime.identifier
    else:
        provider = anime.provider
        identifier = anime.identifier

    uniqueid = _get_uid(anime, dub)
    entry = seasonals.seasonals.get(uniqueid, None)

    if entry is None:
        entry = SeasonalEntry(
            provider=provider,
            identifier=identifier,
            name=anime.name,
            episode=episode,
            dub=dub,
            has_dub=anime.has_dub,
        )
    else:
        entry.episode = episode

    seasonals.seasonals[uniqueid] = entry
    seasonals.write()


def _get_uid(anime: Union["Anime", SeasonalEntry], dub: bool):
    if isinstance(anime, Anime):
        return f"{anime.provider.NAME}:{'dub' if dub else 'sub'}:{anime.identifier}"
    else:
        return f"{anime.provider}:{'dub' if dub else 'sub'}:{anime.identifier}"


def _migrate_seasonals():
    import json
    import re

    season_file = Config()._seasonal_file_path
    old_data = json.load(season_file.open("r"))
    new_seasonals = Seasonals({})

    for k, v in old_data.items():
        name = k
        name = re.sub(r"\s?\((dub|japanese\sdub)\)", "", name, flags=re.IGNORECASE)
        identifier = Path(v["category_url"]).name
        is_dub = identifier.endswith("-dub") or identifier.endswith("-japanese-dub")
        identifier = identifier.removesuffix("-dub").removesuffix("-japanese-dub")
        episode = v["ep"]
        unique_id = f"gogoanime:{'dub' if is_dub else 'sub'}:{identifier}"

        new_entry = SeasonalEntry(
            provider="gogoanmie",
            name=name,
            identifier=identifier,
            episode=episode,
            dub=is_dub,
            has_dub=is_dub,
        )

        new_seasonals.seasonals[unique_id] = new_entry

    new_seasonals.write()
    return new_seasonals
