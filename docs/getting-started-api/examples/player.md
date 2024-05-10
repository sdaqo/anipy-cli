## Video Playback
In general there are two types of players, the ones that are run as a subprocess and the other ones. The ones run with in a subprocess base upon [SubProcessPlayerBase][anipy_api.player.base.SubProcessPlayerBase] (this bases on [PlayerBase][anipy_api.player.base.PlayerBase]) and the other ones straight upon the [PlayerBase][anipy_api.player.base.PlayerBase], you have to consider that both may take different arguments!

For all available players please check out [this](../../availabilty.md#current-version) page or use the [list_players][anipy_api.player.player.list_players] function!

```python
from anipy_api.player import get_player
from anipy_api.anime import Anime
from anipy_api.provider import ProviderStream, LanguageTypeEnum

def on_play(anime: Anime, stream: ProviderStream):
    print("Now playing episode {stream.episode} from {anime.name}!")

mpv_player = get_player( # (1)
    "/usr/bin/mpv",
    extra_args=["--fs"],
    play_callback=on_play
)

anime = ...
stream = anime.get_video(
    episode=1,
    lang=LanguageTypeEnum.SUB,
    preferred_quality="worst"
)

mpv_player.play_title(anime, stream)
mpv_player.wait()
mpv_player.play_file("/some/file.mp4") # (2)
```

1. You can also use the [list_players][anipy_api.player.player.list_players] function to get a list of players.
2. With the [play_file][anipy_api.player.base.PlayerBase.play_file] function you can play local files.

You can also use the mpv-controllable player, it wraps the [python-mpv](https://github.com/jaseg/python-mpv?tab=readme-ov-file#usage) 
player which uses libmpv, check python-mpv's readme to know how to get libmpv. This allows you to controll the player in the code, check this out:
```python
from anipy_api.player import get_player, list_players
from anipy_api.anime import Anime
from anipy_api.provider import ProviderStream, LanguageTypeEnum

def on_play(anime: Anime, stream: ProviderStream):
    print("Now playing episode {stream.episode} from {anime.name}!")

mpv_controllable_player = get_player(
    "mpv-controllable",
    play_callback=on_play 
    # (1)
)

anime = ...
stream = anime.get_video(
    episode=1,
    lang=LanguageTypeEnum.SUB,
    preferred_quality="worst"
)

mpv_controllable_player.play_title(anime, stream)
mpv_player.mpv.seek(10) # (2)
mpv_player.wait()
```

1. This player does not accept the extra_args argument, but it does allow you to override arguments passed to the MPV object, for that use the [MpvControllable][anipy_api.player.players.mpv_control.MpvControllable] class directly.
2. This, for example, seeks the player by 10 seconds. Check out the other functions of the controllable mpv instance in the python-mpv repo or use your LSP!
