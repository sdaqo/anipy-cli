from dataclasses import dataclass, field, fields
from pathlib import Path
from time import time
from typing import TYPE_CHECKING, Dict, Optional, Protocol, Set, Union


from dataclasses_json import DataClassJsonMixin, config

from anipy_api.provider import Episode, LanguageTypeEnum

if TYPE_CHECKING:
    from anipy_api.anime import Anime


@dataclass
class LocalListEntry(DataClassJsonMixin):
    """A json-serializable local list entry class that can be saved to a file
    and includes various information to rebuild state after deserializing.

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
class LocalListData(DataClassJsonMixin):
    """A json-serializable class to save local list data

    Attributes: 
        data: The dict with the data, this is always "uid: value". The uid is "{provider}:{identifier}"
    """
    data: Dict[str, LocalListEntry]

    def write(self, file: Path):
        """Writes the data of the current LocalListData object to a file.

        Args:
            file: File path to write to (this should be a .json file)
        """
        file.write_text(self.to_json())



class MigrateCallback(Protocol):
    """Callback that gets called upon a KeyError while loading a file in the LocalList class,
    in a attempt to migrate data that may be in an old format. This callback should either return
    a migrated LocalListData object or a empty LocalListData object if migration fails (could also just raise a exception).
    """

    def __call__(self, file: Path) -> LocalListData: 
        """
        Args:
            file: The file path that is passed to the callback to migrate
        """
        ...

class LocalList:
    """This class can manage a list of Anime objects and some extra state. This is more
    for the cli, but it may also be used in a library for easy (de)serialization of Anime objects"""
    def __init__(self, file: Path, migrate_cb: Optional[MigrateCallback] = None):
        """__init__ of LocalList

        Args:
            file: Path of the list
            migrate_cb: Migration callback, look at [anipy_api.locallist.MigrateCallback]
        """

        if not file.is_file():
            file.parent.mkdir(exist_ok=True, parents=True)
            self.data = LocalListData({})

        try:
            self.data = LocalListData.from_json(file.read_text())
        except KeyError:
            if migrate_cb is None:
                raise

            self.data = migrate_cb(file)
            
    
    def update(self, anime: Union[Anime, LocalListEntry], **update_fields) -> Optional[LocalListEntry]:
        uid = self._get_uid(anime)
        entry = self.data.data.get(uid, None)

        if entry is None:
            return entry

        entry_dict = entry.to_dict()

        for k, v in update_fields.items():
            try:
                entry_dict[k] = v
            except KeyError:
                continue

        entry = LocalListEntry.from_dict(entry_dict)
        self.data.data[uid] = entry

        return entry

    
    def delete(self, anime: Union[Anime, LocalListEntry]) -> Optional[LocalListEntry]:
        return self.data.data.pop(self._get_uid(anime), None)

    def get(self, anime: Anime) -> Optional[LocalListEntry]:
        return self.data.data.get(self._get_uid(anime), None)
    
    @staticmethod
    def _get_uid(anime: Union[Anime, LocalListEntry]) -> str:
        if isinstance(anime, Anime):
            provider = anime.provider.NAME
            identifier = anime.identifier
        elif isinstance(anime, LocalListEntry):
            provider = anime.provider
            identifier = anime.identifier
        else:
            raise TypeError(f"{type(anime)} can not be interpreted as a Anime or LocalListEntry")

        return f"{provider}:{identifier}"
