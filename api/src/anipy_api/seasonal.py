"""Manage seasonals data.

This is more thought for the cli, but it may also be used in a library
for easy (de)serialization of Anime objects
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional, Set, Union

from dataclasses_json import DataClassJsonMixin, config

from anipy_api.anime import Anime
from anipy_api.provider import Episode, LanguageTypeEnum


@dataclass
class SeasonalEntry(DataClassJsonMixin):
    """A json-serializable seasonal entry class that is saved to a seasonals
    file and includes various information to rebuild the state after
    deserializing.

    Attributes:
        provider: The provider of the anime
        identifier: The identifier of the anime
        name: The name of the anime
        episode: The current episode
        language: The language that the anime was in
        languages: A list of languages the anime supports
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
    """A json-serializable seasonals class that holds a dictonary of seasonal
    entries.

    Attributes:
        seasonals: A dict of seasonal entries. The key is composed of the name of the provider and the anime identifier creating a "unique id" the format is this: "{provider_name}:{anime_identifier}"
    """

    seasonals: Dict[str, SeasonalEntry]

    def write(self, file: Path):
        """Writes the seasonals of the current Seasonals object to a file.

        Args:
            file: Seasonals file path (this should be a .json file)
        """
        file.write_text(self.to_json())

    @staticmethod
    def read(file: Path) -> "Seasonals":
        """Read the contents of a seasonals file.

        Args:
            file: Seasonals file path (this should be a .json file)

        Returns:
            Seasonals object
        """
        if not file.is_file():
            file.parent.mkdir(exist_ok=True, parents=True)
            return Seasonals({})

        try:
            seasonals: Seasonals = Seasonals.from_json(file.read_text())
        except KeyError:
            seasonals = _migrate_seasonals(file)

        return seasonals


def get_seasonals(file: Path) -> Seasonals:
    """Same as Seasonals.read(file)

    Args:
        file: Seasonals file path (this should be a .json file)

    Returns:
        Seasonals object
    """
    return Seasonals.read(file)


def get_seasonal_entry(file: Path, anime: "Anime") -> Optional[SeasonalEntry]:
    """Get a specific seasonal entry.

    Args:
        file: Seasonals file path (this should be a .json file)
        anime: Anime to get the seasonal entry from

    Returns:
        A SeasonlEntry object if the anime is in history, returns None otherwise
    """
    seasonals = Seasonals.read(file)

    return seasonals.seasonals.get(_get_uid(anime), None)


def delete_seasonal(file: Path, anime: Union["Anime", SeasonalEntry]):
    """Delete a seasonal from a file.

    Args:
        file: Seasonals file path (this should be a .json file)
        anime: Anime to delete
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
    """Update a specific history entry's episode and language.

    Args:
        file: Seasonals file path (this should be a .json file)
        anime: Anime to update
        episode: Updated episode
        lang: Updated language of the anime
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
