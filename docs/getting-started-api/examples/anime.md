## Representing an anime

On the last page we learned how to use the provider to search for anime. This
page covers the [Anime](anipy_api.anime.Anime) class, it always represents a
single anime.

## How to get an Anime object

```python
from anipy_api.anime import Anime

provider = ... # (1)
results = provider.get_search("frieren")

anime = []

for r in results:
    anime.append(Anime.from_search_result(provider, r))
    # or if you really want:
    anime.append(Anime(provider, r.name, r.identifier, r.languages))
```

1. The provider, check the [provider page](provider.md).

## Get episodes

A [Episode][anipy_api.provider.base.Episode] is either an integer or a float
(for .5 episodes).

```python
from anipy_api.provider import LanguageTypeEnum

anime = ...
# List of Episode-type numbers
episodes = anime.get_episodes(lang=LanguageTypeEnum.SUB) # (1)
```

1. For episodes and videos you have to always specify the language type you want
   to get the episodes/videos in. To check which languages the anime supports,
   check the `languages` attribute of the anime. 
   If the language type you provide is not supported by the anime both the methods for getting episodes and video streams
   will throw a [LangTypeNotAvailableError][anipy_api.error.LangTypeNotAvailableError] error.

## Get video streams

Either use [get_video][anipy_api.anime.Anime.get_video] or
[get_videos][anipy_api.anime.Anime.get_videos], the difference is that one
filters out 1 stream based on quality. Both return
[ProviderStream][anipy_api.provider.base.ProviderStream] objects.

```python
from anipy_api.provider import LanguageTypeEnum

anime = ...

episode_1_stream = anime.get_video(
    episode=1, 
    lang=LanguageTypeEnum.SUB,
    preferred_quality=720 # (1)
)
# or get a list of streams that you can filter yourself
episode_1_streams = anime.get_videos(1, LanguageTypeEnum.SUB)
```

1. Check the [reference][anipy_api.anime.Anime.get_video] for information about
   the `preferred_quality` argument.


## Get anime info
The `get_info` method returns a [PoviderInfoResult][anipy_api.provider.ProviderInfoResult] object.
```python
anime = ...
info = anime.get_info() # (1)

print(f"The anime's name is {info.name} and it has these genres: {info.genres}!")
```

1. You do not need to specify the language for the info, because it is expected to be the same for both sub and dub.

## What now?
Keep your [ProviderStream][anipy_api.provider.base.ProviderStream] objects and move on to [3. Downloader](downloader.md) or [4. Player](player.md)!
