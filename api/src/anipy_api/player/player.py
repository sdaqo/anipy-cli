from pathlib import Path
from typing import TYPE_CHECKING, List, Optional

from anipy_api.error import PlayerError
from anipy_api.player.players import Mpv, Syncplay, Vlc

if TYPE_CHECKING:
    from pypresence import Presence

    from anipy_api.player.base import PlayerBase


def get_player(
    player: Path,
    extra_args: List[str] = [],
    rpc_client: Optional["Presence"] = None,
) -> "PlayerBase":
    if Path(player.name).stem == "mpv-controlled":
        from anipy_api.player.players.mpv_control import MpvControllable

        return MpvControllable(rpc_client=rpc_client)

    player_dict = {"mpv": Mpv, "mpvnet": Mpv, "vlc": Vlc, "syncplay": Syncplay}

    player_class = player_dict.get(Path(player.name).stem, None)

    if player_class:
        return player_class(str(player), extra_args=extra_args, rpc_client=rpc_client)
    else:
        raise PlayerError(f"Specified player `{player}` is unknown")
