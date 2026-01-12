## Why?

Uhm, I did not find a proper implementation of the MyAnimeList v2 api for
python... so yeah.

There is also support for [anilist](https://anilist.co/), the usage is generally the same,
exepect for authentication. 
For the API docs please see [AniList][anipy_api.anilist.AniList] and [AniListAdapter][anipy_api.anilist.AniListAdapter] 
also check [anilist_cli.py](https://github.com/sdaqo/anipy-cli/blob/master/cli/src/anipy_cli/clis/anilist_cli.py) for a implementation example.
    
## Authentication

The [MyAnimeList][anipy_api.mal.MyAnimeList] class implement basic
authentication via a username/password combo or via a refresh token.

```python
from anipy_api.mal import MyAnimeList

# password
mal = MyAnimeList.from_password_grant( # (1)
    user="test",
    password="test",
    client_id=None # (2)
)
# or refresh token
mal = MyAnimeList.from_rt_grant(
    refresh_token="random-gibberish112mnsd8123109",
    client_id="more-random-suff1231283123102938" # (3)
)
```

1. Those functions may throw a
   [MyAnimeListError][anipy_api.error.MyAnimeListError] when auth fails, wrap
   them in a try/except.
2. Please note that that currently no complex oauth autentication scheme is
   implemented, this client uses the client id of the official MyAnimeList
   android app, this gives us the ability to login via a username/password
   combination. If you pass your own client id you will not be able to use the
   from_password_grant function.
3. Here you can pass the client id like normal.

## Usage

```python
from anipy_api.mal import MyAnimeList, MALMyListStatusEnum
mal = ...

frieren = mal.get_anime(52991)
print(frieren.title)

results = mal.get_search( # (1)
    "frieren",
    limit=20, # (2)
    pages=2 # (3)
)
print(results)

user = mal.get_user() # (4)
print(user)

updated_entry = mal.update_anime_list( # (5)
    52991,
    status=MALMyListStatusEnum.WATCHING,
    watched_episodes=2,
    tags=["currently-updated"] # (6)
)
print(updated_entry)

frieren_now = mal.get_anime(52991) # (7)
frieren_now.my_list_status.tags # -> ["currently-updated"]

user_watching = mal.get_anime_list(
    status_filter=MALMyListStatusEnum.WATCHING # (8)
)
print(user_list)

mal.remove_from_anime_list(52991)
```

1. All these functions may also return a
   [MyAnimeListError][anipy_api.error.MyAnimeListError] on for example a http
   error.
2. Specify the limit per page returned.
3. The number of pages returned, note that the amount of anime returned is
   `limit * pages`.
4. This get information about the current user.
5. This function either updates or adds the anime to the user's list if it does
   not already exists.
6. Note that this will override all the tags already set before!
7. Now that the anime is added to the list, get it again and the
   `my_list_status` attribute will not be `None` anymore.
8. The `status_filter` attribute filters for a user list status.

## Adapting between provider anime and MyAnimeList anime

Ok so this is the important part. Imagaine you have a provider anime and want to
add that to your myanimelist, but you do not know which mal anime that is. The
[MyAnimeListAdapter][anipy_api.mal.MyAnimeListAdapter] class can handle that for
you.

BUT this does not always work, there is a possibilty that the adapter can not
match the anime, this class uses the
[Levenshtein Distance](https://en.wikipedia.org/wiki/Levenshtein_distance)
algorithm to calculate the similiarty between names, you can tweak its
parameters and also other stuff to ensure you get a match.

```python
from anipy_api.mal import MyAnimeListAdapter

mal = ...
provider = ... # (1)

adapter = MyAnimeListAdapter(mal, provider)

# Provider -> MyAnimeList
anime = ...
mal_anime = adapter.from_provider(
    anime,
    minimum_similarity_ratio=0.8, # (2)
    use_alternative_names=True # (3)
)
if mal_anime is not None:
    print(mal_anime)

# MyAnimeList -> Provider
mal_anime = ...
anime = adapter.from_myanimelist(
    mal_anime,
    minimum_similarity_ratio=0.8,
    use_alternative_names=True,
    use_filters=True # (4)
)
if anime is not None:
    print(anime)
```

1. The provider to or from which you want to adapt.
2. The minimum accepted similarity ratio. This should be a number from 0-1, 1
   meaning the names are identical 0 meaning there are no identical charachters
   whatsoever. If it is not met the function will return None.
3. With this the alternative names will also be checked if available. This
   improves chances of matching but may take longer.
4. You may remember the section about filters, this argument will use filters
   for the provider to cut down on possible wrong results, do note that this
   will take more time.
