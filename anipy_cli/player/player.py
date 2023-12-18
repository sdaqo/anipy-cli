import sys
from typing import TypeVar
from pathlib import Path

from anipy_cli.config import Config
from anipy_cli.misc import error
from anipy_cli.player.players import Mpv, Vlc, Syncplay
from anipy_cli.player.players.base import PlayerBase

PlayerBaseType = TypeVar("PlayerBaseType", bound=PlayerBase)


def get_player(rpc_client=None, player_override="") -> PlayerBaseType:
    cfg = Config()

    player = player_override

    if not player_override:
        player = cfg.player_path
    
    player = Path(player)
    
    if player.name == "mpv" and cfg.reuse_mpv_window:
        from anipy_cli.player.players.mpv_contrl import MpvControllable
        return MpvControllable(rpc_client=rpc_client)

    player_dict = {
        "mpv": Mpv,
        "mpvnet": Mpv,
        "vlc": Vlc,
        "syncplay": Syncplay
    }

    player_class = player_dict.get(player.name, None)
    
    if player_class:
        return player_class(str(player), rpc_client=rpc_client)
    else:
        error(f"Specified player `{player}` is unknown")
        sys.exit()
