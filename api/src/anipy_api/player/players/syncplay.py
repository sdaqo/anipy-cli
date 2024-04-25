from typing import List
from anipy_api.player.base import SubProcessPlayerBase

class Syncplay(SubProcessPlayerBase):
    def __init__(self, player_path: str, extra_args: List[str] = [], rpc_client=None):
        self.player_exec = "syncplay"
        player_args_template = [
            "--",
            "--meta-title='{media_title}'",
            "{stream_url}",
            *extra_args
        ]

        super().__init__(
            rpc_client=rpc_client,
            player_path=player_path,
            player_args_template=player_args_template,
        )
