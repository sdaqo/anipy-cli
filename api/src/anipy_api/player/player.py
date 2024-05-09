from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Iterator, Type

from anipy_api.error import PlayerError
from anipy_api.player.players import *
from anipy_api.player.players import __all__

if TYPE_CHECKING:
    from anipy_api.player.base import PlayerBase, PlayCallback


def list_players() -> Iterator[Type["PlayerBase"]]:
    """List all available players. Note that is not really useful as not all of them have the same `__init__` signature, better use [get_player][anipy_api.player.player.get_player] or directly import the players you want to use.

    Yields:
        Player classes (that still need to be initialized)
    """
    for p in __all__:
        yield globals()[p]


def get_player(
    player: Path,
    extra_args: List[str] = [],
    play_callback: Optional["PlayCallback"] = None,
) -> "PlayerBase":
    """Get a fitting player class based on a player path.

    Args:
        player: Path to the player
        extra_args: Extra arguments to pass to players that support it
        play_callback: Callback called upon starting to play a title with `play_title`

    Raises:
        PlayerError: If the player is not found

    Returns:
        The player class
    """
    if Path(player.name).stem == "mpv-controlled":
        return MpvControllable(play_callback=play_callback)

    player_dict = {"mpv": Mpv, "mpvnet": Mpv, "vlc": Vlc, "syncplay": Syncplay}

    player_class = player_dict.get(Path(player.name).stem, None)

    if player_class:
        return player_class(
            str(player), extra_args=extra_args, play_callback=play_callback
        )
    else:
        raise PlayerError(f"Specified player `{player}` is unknown")
