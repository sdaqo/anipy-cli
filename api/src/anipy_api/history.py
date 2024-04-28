"""Manage history data.

This is more thought for the cli, but it may also be used in a library
for easy (de)serialization of Anime objects
"""

from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import TYPE_CHECKING, Dict, Optional, Set

from dataclasses_json import DataClassJsonMixin, config

from anipy_api.provider import Episode, LanguageTypeEnum

if TYPE_CHECKING:
    from anipy_api.anime import Anime


@dataclass
class HistoryEntry(DataClassJsonMixin):
    """A json-serializable history entry class that is saved to a history file
    and includes various information to rebuild the state after deserializing.

    Attributes:
        provider: The provider of the anime
        identifier: The identifier of the anime
        name: The name of the anime
        episode: The current episode
        timestamp: The timestamp when this entry got updated/created (for sorting)
        language: The language that the anime was in
        languages: A list of languages the anime supports
    """

    provider: str = field(metadata=config(field_name="pv"))
    identifier: str = field(metadata=config(field_name="id"))
    name: str = field(metadata=config(field_name="na"))
    episode: Episode = field(metadata=config(field_name="ep"))
    timestamp: int = field(metadata=config(field_name="ts"))
    language: LanguageTypeEnum = field(metadata=config(field_name="lg"))
    languages: Set[LanguageTypeEnum] = field(metadata=config(field_name="ls"))

    def __repr__(self) -> str:
        return f"{self.name} ({self.language}) Episode {self.episode}"

    def __hash__(self) -> int:
        return hash(f"{self.provider}:{self.identifier}")


@dataclass
class History(DataClassJsonMixin):
    """A json-serializable history class that holds a dictonary of history
    entries.

    Attributes:
        history: A dict of history entries. The key is composed of the name of the provider and the anime identifier creating a "unique id" the format is this: "{provider_name}:{anime_identifier}"
    """

    history: Dict[str, HistoryEntry]

    def write(self, file: Path):
        """Writes the history of the current History object to a file.

        Args:
            file: History file path (this should be a .json file)
        """
        file.write_text(self.to_json())

    @staticmethod
    def read(file: Path) -> "History":
        """Read the contents of a history file.

        Args:
            file: History file path (this should be a .json file)

        Returns:
            History object
        """
        if not file.is_file():
            file.parent.mkdir(exist_ok=True, parents=True)
            return History({})

        try:
            history: History = History.from_json(file.read_text())
        except KeyError:
            history = _migrate_history(file)

        return history


def get_history(file: Path) -> History:
    """Same as History.read(file)

    Args:
        file: History file path (this should be a .json file)

    Returns:
        History object
    """
    return History.read(file)


def get_history_entry(file: Path, anime: "Anime") -> Optional[HistoryEntry]:
    """Get a specific history entry.

    Args:
        file: History file path (this should be a .json file)
        anime: Anime to get the history entry from

    Returns:
        A HistoryEntry object if the anime is in history, returns None otherwise
    """
    history = History.read(file)
    uniqueid = _get_uid(anime)

    return history.history.get(uniqueid, None)


def update_history(
    file: Path, anime: "Anime", episode: "Episode", lang: LanguageTypeEnum
):
    """Update a specific history entry's episode and language.

    Args:
        file: History file path (this should be a .json file)
        anime: Anime to update the history of
        episode: Updated episode
        lang: Updated language of the anime
    """
    history = History.read(file)

    uniqueid = _get_uid(anime)
    entry = history.history.get(uniqueid, None)

    if entry is None:
        entry = HistoryEntry(
            provider=anime.provider.NAME,
            identifier=anime.identifier,
            name=anime.name,
            episode=episode,
            timestamp=int(time()),
            language=lang,
            languages=anime.languages,
        )
    else:
        entry.episode = episode
        entry.timestamp = int(time())
        entry.language = lang

    history.history[uniqueid] = entry

    history.write(file)


def _get_uid(anime: "Anime"):
    return f"{anime.provider.NAME}:{anime.identifier}"


def _migrate_history(file):
    import json
    import re

    old_data = json.load(file.open("r"))
    new_history = History({})

    for k, v in old_data.items():
        name = k
        name = re.sub(r"\s?\((dub|japanese\sdub)\)", "", name, flags=re.IGNORECASE)
        identifier = Path(v["category-link"]).name
        is_dub = identifier.endswith("-dub") or identifier.endswith("-japanese-dub")
        identifier = identifier.removesuffix("-dub").removesuffix("-japanese-dub")
        episode = v["ep"]
        timestamp = int(time())
        unique_id = f"gogoanime:{'dub' if is_dub else 'sub'}:{identifier}"

        new_entry = HistoryEntry(
            provider="gogoanmie",
            name=name,
            identifier=identifier,
            episode=episode,
            timestamp=timestamp,
            language=LanguageTypeEnum.DUB if is_dub else LanguageTypeEnum.SUB,
            languages={LanguageTypeEnum.DUB if is_dub else LanguageTypeEnum.SUB},
        )

        new_history.history[unique_id] = new_entry

    new_history.write(file)
    return new_history
