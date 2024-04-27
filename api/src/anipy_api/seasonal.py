from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Union

from dataclasses_json import DataClassJsonMixin, config

from anipy_api.anime import Anime
from anipy_api.provider import Episode, LanguageTypeEnum


@dataclass
class SeasonalEntry(DataClassJsonMixin):
    """

    Attributes: 
        provider: 
        identifier: 
        name: 
        episode: 
        language: 
        languages: 
    """
    provider: str = field(metadata=config(field_name="pv"))
    identifier: str = field(metadata=config(field_name="id"))
    name: str = field(metadata=config(field_name="na"))
    episode: Episode = field(metadata=config(field_name="ep"))
    language: LanguageTypeEnum = field(metadata=config(field_name="lg"))
    languages: Set[LanguageTypeEnum] = field(metadata=config(field_name="ls"))

    def __repr__(self) -> str:
        return f"{self.name} ({self.language}) Episode {self.episode}"

    def __hash__(self) -> int:
        return hash(_get_uid(self))


@dataclass
class Seasonals(DataClassJsonMixin):
    """

    Attributes: 
        seasonals: 
    """
    seasonals: Dict[str, SeasonalEntry]

    def write(self, file: Path):
        file.write_text(self.to_json())

    @staticmethod
    def read(file: Path) -> "Seasonals":
        if not file.is_file():
            file.parent.mkdir(exist_ok=True, parents=True)
            return Seasonals({})

        try:
            seasonals: Seasonals = Seasonals.from_json(file.read_text())
        except KeyError:
            seasonals = _migrate_seasonals(file)

        return seasonals


def get_seasonals(file: Path) -> Seasonals:
    """

    Args:
        file: 

    Returns:
        
    """
    return Seasonals.read(file)


def get_seasonal_entry(file: Path, anime: "Anime") -> Optional[SeasonalEntry]:
    """

    Args:
        file: 
        anime: 

    Returns:
        
    """
    seasonals = Seasonals.read(file)

    return seasonals.seasonals.get(_get_uid(anime), None)


def delete_seasonal(file: Path, anime: Union["Anime", SeasonalEntry]):
    """

    Args:
        file: 
        anime: 
    """
    """

    Args:
        file: 
        anime: 
    """
    seasonals = Seasonals.read(file)

    seasonals.seasonals.pop(_get_uid(anime))
    seasonals.write(file)


def update_seasonal(
    file: Path,
    anime: Union["Anime", SeasonalEntry],
    episode: "Episode",
    lang: LanguageTypeEnum,
):
    """

    Args:
        file: 
        anime: 
        episode: 
        lang: 
    """
    seasonals = Seasonals.read(file)

    if isinstance(anime, Anime):
        provider = anime.provider.NAME
        identifier = anime.identifier
    else:
        provider = anime.provider
        identifier = anime.identifier

    uniqueid = _get_uid(anime)
    entry = seasonals.seasonals.get(uniqueid, None)

    if entry is None:
        entry = SeasonalEntry(
            provider=provider,
            identifier=identifier,
            name=anime.name,
            episode=episode,
            language=lang,
            languages=anime.languages,
        )
    else:
        entry.episode = episode
        entry.language = lang

    seasonals.seasonals[uniqueid] = entry
    seasonals.write(file)


def _get_uid(anime: Union["Anime", SeasonalEntry]):
    if isinstance(anime, Anime):
        return f"{anime.provider.NAME}:{anime.identifier}"
    else:
        return f"{anime.provider}:{anime.identifier}"


def _migrate_seasonals(file):
    import json
    import re

    old_data = json.load(file.open("r"))
    new_seasonals = Seasonals({})

    for k, v in old_data.items():
        name = k
        name = re.sub(r"\s?\((dub|japanese\sdub)\)", "", name, flags=re.IGNORECASE)
        identifier = Path(v["category_url"]).name
        is_dub = identifier.endswith("-dub") or identifier.endswith("-japanese-dub")
        identifier = identifier.removesuffix("-dub").removesuffix("-japanese-dub")
        episode = v["ep"]
        unique_id = f"gogoanime:{identifier}"

        new_entry = SeasonalEntry(
            provider="gogoanmie",
            name=name,
            identifier=identifier,
            episode=episode,
            language=LanguageTypeEnum.DUB if is_dub else LanguageTypeEnum.SUB,
            languages={LanguageTypeEnum.DUB if is_dub else LanguageTypeEnum.SUB},
        )

        new_seasonals.seasonals[unique_id] = new_entry

    new_seasonals.write(file)
    return new_seasonals
