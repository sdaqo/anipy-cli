from typing import TYPE_CHECKING, Optional
from pathlib import Path

from anipy_cli.config import Config
from anipy_cli.player.players import Mpv, Vlc, Syncplay
from anipy_cli.error import PlayerError

if TYPE_CHECKING:
    from anipy_cli.player.players.base import PlayerBase


def get_player(rpc_client=None, player_override: Optional[str] = None) -> "PlayerBase":
    cfg = Config()

    player = cfg.player_path

    if player_override is not None:
        player = player_override

    player = Path(player)

    if Path(player.name).stem == "mpv" and cfg.reuse_mpv_window:
        from anipy_cli.player.players.mpv_control import MpvControllable

        return MpvControllable(rpc_client=rpc_client)

    player_dict = {"mpv": Mpv, "mpvnet": Mpv, "vlc": Vlc, "syncplay": Syncplay}

    player_class = player_dict.get(Path(player.name).stem, None)

    if player_class:
        return player_class(str(player), rpc_client=rpc_client)
    else:
        raise PlayerError(f"Specified player `{player}` is unknown")
