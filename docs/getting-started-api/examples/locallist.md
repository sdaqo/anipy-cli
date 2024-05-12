## Serializing and de-serializing anime

The local lists feature is more a feature meant for the cli, but you may use it
for easy (de-) serialization of [Anime][anipy_api.anime.Anime] objects including
some extra state data for tracking progress.

## Usage

All the data is stored in json format.

```python
from anipy_api.locallist import LocalList
from anipy_api.provider import LanguageTypeEnum
from anipy_api.anime import Anime

local_list = LocalList(
    "/path/to/list.json",
    migrate_cb=None # (1)
)

anime = ...

# Adding an anime
entry = local_list.update(anime, episode=1, language=LanguageTypeEnum.SUB) # (2)

# Updating it
updated_entry = local_list.update(anime, episode=2) # (3)

# Get entry for anime
entry = local_list.get(anime)

# Get all entries in file
entries = [
    Anime.from_local_list_entry(entry)
    for entry in local_list.get_all() # (4)
]

# Delete entry
delted_entry = local_list.delete(anime) # (5)
```

1. Optionally, you may pass a migration callback. This gets called if parsing
   the data of the json file into the data format fails. Check out
   [MigrateCallback][anipy_api.locallist.MigrateCallback].
2. The fields you can pass (after the anime argument) correspond to the fields
   in [LocalListEntry][anipy_api.locallist.LocalListEntry]. When adding an anime
   make sure you are always passing at least the episode and language fields.
3. The anime argument can be a [Anime][anipy_api.anime.Anime] or a
   [LocalListEntry][anipy_api.locallist.LocalListEntry] object, meaning we could
   also pass `entry` here instead of `anime`.
4. You can use
   [Anime.from_local_list_entry][anipy_api.anime.Anime.from_local_list_entry] to
   convert a local list entry into an Anime object
5. Again here you can pass both [Anime][anipy_api.anime.Anime] and
   [LocalListEntry][anipy_api.locallist.LocalListEntry].
