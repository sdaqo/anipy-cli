from dataclasses import dataclass
from dataclasses_json import dataclass_json
from typing import Dict, Optional

from anipy_cli.config import Config
from anipy_cli.provider import Episode
from anipy_cli.anime import Anime

@dataclass_json
@dataclass
class HistoryEntry:
    pv: str
    id: str
    ep: Episode

@dataclass_json
@dataclass
class History:
    history: Dict[str, HistoryEntry]


def get_history() -> Dict[str, HistoryEntry]:
    hist_file = Config().history_file_path

    if not hist_file.is_file():
        return {}
        
    history = History.from_json(hist_file.read_text())

    return history.history


def get_history_entry(anime: Anime) -> Optional[HistoryEntry]:
    history = get_history()
    uniqueid = f"{anime.provider.name()}:{anime.identifier}"

    return history.get(uniqueid, None)


def update_history(anime: Anime, episode: Episode):
    hist_file = Config().history_file_path
    history = get_history()
    
    uniqueid = f"{anime.provider.name()}:{anime.identifier}"
    entry = history.get(uniqueid, None)

    if entry is None:
        entry = HistoryEntry(anime.provider.name(), anime.identifier, episode)
        history[uniqueid] = entry

    hist_file.write_text(History(history=history).to_json())
