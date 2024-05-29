from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Dict, Optional, Protocol, Set, Union, List


from anipy_api.error import ArgumentError
from dataclasses_json import DataClassJsonMixin, config

from anipy_api.provider import Episode, LanguageTypeEnum
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
    """This class can manage a list of Anime objects and some extra state. This is built
    for the cli, but it may also be used in a library for easy (de)serialization of Anime objects
    """

    def __init__(self, file: Path, migrate_cb: Optional[MigrateCallback] = None):
        """__init__ of LocalList

        Args:
            file: Path of the list
            migrate_cb: Migration callback, look at [MigrateCallback][anipy_api.locallist.MigrateCallback]
        """

        self.file = file
        if not self.file.is_file():
            self.file.parent.mkdir(exist_ok=True, parents=True)
            self.file.touch()
            self.data = LocalListData({})
            self.data.write(self.file)
        else:
            try:
                self.data = LocalListData.from_json(self.file.read_text())
            except KeyError:
                if migrate_cb is None:
                    raise
                self.data = migrate_cb(self.file)

    def _read(self):
        self.data = LocalListData.from_json(self.file.read_text())

    def update(
        self, anime: Union[Anime, LocalListEntry], **update_fields
    ) -> LocalListEntry:
        """Update (or add) an anime in the local list.

        Example:
            ```python
            from anipy_api.anime import Anime
            from anipy_api.locallist import LocalList
            from anipy_api.provider import LanguageTypeEnum

            anime = Anime(...)
            local_list = LocalList(...)

            # Adding an anime (1)
            local_list.update(anime, episode=1, language=LanguageTypeEnum.SUB)

            # Updating it (2)
            local_list.update(anime, episode=2)
            ```

            1. When adding a anime make sure you are always passing at least the `episode` and `language` fields.
            2. When the anime is already added you can pass any update fields specified in the [LocalListEntry][anipy_api.locallist.LocalListEntry] class.

        Args:
            anime: The anime to update/add, this can be a [Anime][anipy_api.anime.Anime] or [LocalListEntry][anipy_api.locallist.LocalListEntry] object
            **update_fields: The fields to update, they correspond to the fields in [LocalListEntry][anipy_api.locallist.LocalListEntry]

        Returns:
            The updated entry

        Raises:
            ArgumentError: Raised if updating a anime that does not exist (adding) and not providing at
                least the `episode` and `language` to the update_fields.
        """
        self._read()

        uid = self._get_uid(anime)
        entry = self.data.data.get(uid, None)

        if entry is None:
            if not ("episode" in update_fields and "language" in update_fields):
                raise ArgumentError(
                    "The anime you are trying to update is not added to the list and you are not"
                    "providing the neccessary update_fields `episode` and `language`, this can not be processed"
                )

            entry = LocalListEntry(
                provider=str(anime.provider),
                identifier=anime.identifier,
                name=anime.name,
                timestamp=int(time()),
                episode=update_fields["episode"],
                language=update_fields["language"],
                languages=anime.languages,
            )
        else:
            entry_dict = entry.to_dict()

            for k, v in update_fields.items():
                try:
                    entry_dict[k] = v
                except KeyError:
                    continue

            entry = LocalListEntry.from_dict(entry_dict)
            entry.timestamp = int(time())

        self.data.data[uid] = entry
        self.data.write(self.file)

        return entry

    def delete(self, anime: Union[Anime, LocalListEntry]) -> Optional[LocalListEntry]:
        """Delete a entry from the local list.

        Args:
            anime: The anime to delete this can be a [Anime][anipy_api.anime.Anime] or [LocalListEntry][anipy_api.locallist.LocalListEntry] object

        Returns:
            The deleted object or None if the anime to delete was not found in the local list
        """
        self._read()

        entry = self.data.data.pop(self._get_uid(anime), None)
        self.data.write(self.file)

        return entry

    def get(self, anime: Anime) -> Optional[LocalListEntry]:
        """Get a specific local list entry.

        Args:
            anime: The anime to get the local list entry from

        Returns:
            A local list entry if it exists for the provided anime

        """
        self._read()

        return self.data.data.get(self._get_uid(anime), None)

    def get_all(self) -> List[LocalListEntry]:
        """Get all of the local list entries.

        Returns:
            A list of all local list entries
        """
        self._read()

        return list(self.data.data.values())

    @staticmethod
    def _get_uid(anime: Union[Anime, LocalListEntry]) -> str:
        if isinstance(anime, Anime):
            provider = anime.provider.NAME
            identifier = anime.identifier
        elif isinstance(anime, LocalListEntry):
            provider = anime.provider
            identifier = anime.identifier
        else:
            raise TypeError(
                f"{type(anime)} can not be interpreted as a Anime or LocalListEntry object"
            )

        return f"{provider}:{identifier}"
