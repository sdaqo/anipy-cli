from pathlib import Path
from dataclasses import dataclass, field
from time import time
from dataclasses_json import dataclass_json, config
from typing import Dict, Optional

from anipy_cli.config import Config
from anipy_cli.provider import Episode
from anipy_cli.anime import Anime


@dataclass_json
@dataclass
class HistoryEntry:
    provider: str = field(metadata=config(field_name="pv"))
    identifier: str = field(metadata=config(field_name="id"))
    name: str = field(metadata=config(field_name="na"))
    episode: Episode = field(metadata=config(field_name="ep"))
    timestamp: int = field(metadata=config(field_name="ts"))

    def __repr__(self) -> str:
        return f"{self.name} episode {self.episode}"


@dataclass_json
@dataclass
class History:
    history: Dict[str, HistoryEntry]

    def write(self):
        hist_file = Config().history_file_path
        hist_file.write_text(self.to_json())

    @staticmethod
    def read() -> "History":
        hist_file = Config().history_file_path

        if not hist_file.is_file():
            hist_file.parent.mkdir(exist_ok=True, parents=True)
            return History({})

        try:
            history: History = History.from_json(hist_file.read_text())
        except KeyError:
            history = _migrate_history()

        return history


def get_history() -> History:
    return History.read()


def get_history_entry(anime: Anime) -> Optional[HistoryEntry]:
    history = History.read()
    uniqueid = f"{anime.provider.NAME}:{anime.identifier}"

    return history.history.get(uniqueid, None)


def update_history(anime: Anime, episode: Episode):
    history = History.read()

    uniqueid = f"{anime.provider.NAME}:{anime.identifier}"
    entry = history.history.get(uniqueid, None)

    if entry is None:
        entry = HistoryEntry(
            provider=anime.provider.NAME,
            identifier=anime.identifier,
            name=anime.name,
            episode=episode,
            timestamp=int(time()),
        )
    else:
        entry.episode = episode
        entry.timestamp = int(time())

    history.history[uniqueid] = entry

    history.write()


def _migrate_history():
    import json

    hist_file = Config().history_file_path
    old_data = json.load(hist_file.open("r"))
    new_history = History({})

    for k, v in old_data.items():
        name = k
        identifier = Path(v["category-link"]).name
        episode = v["ep"]
        timestamp = int(time())
        unique_id = f"gogoanime:{identifier}"
        new_entry = HistoryEntry(
            provider="gogoanmie",
            name=name,
            identifier=identifier,
            episode=episode,
            timestamp=timestamp,
        )

        new_history.history[unique_id] = new_entry

    new_history.write()
    return new_history
