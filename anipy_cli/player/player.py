import sys
from typing import TypeVar

from anipy_cli.config import Config
from anipy_cli.misc import error
from anipy_cli.player.players import Mpv, Vlc, Syncplay
from anipy_cli.player.players.base import PlayerBase

PlayerBaseType = TypeVar('PlayerBaseType', bound=PlayerBase)

def get_player(rpc_client=None, player_override=None) -> PlayerBaseType:
    cfg = Config()

    player = player_override

    if not player_override:
        player = cfg.player_path
    
    if player == "mpv" and cfg.reuse_mpv_window:
        from anipy_cli.player.players import MpvControllable
        return MpvControllable(rpc_client=rpc_client)

    if player in ("mpv", "mpvnet"):
        return Mpv(rpc_client=rpc_client, mpv_exec_name=player)
    elif player == "vlc":
        return Vlc(rpc_client=rpc_client)
    elif player == "synclplay":
        return Syncplay(rpc_client=rpc_client)
    else:
        error(f"Specified player `{player}` is unknown")
        sys.exit()
