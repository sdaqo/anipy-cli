from typing import List
from anipy_api.player.base import SubProcessPlayerBase


class Mpv(SubProcessPlayerBase):
    def __init__(self, player_path: str, extra_args: List[str] = [], rpc_client=None):
        player_args_template = [
            "{stream_url}",
            "--force-media-title={media_title}",
            "--force-window=immediate",
            *extra_args,
        ]

        super().__init__(
            player_args_template=player_args_template,
            player_path=player_path,
            rpc_client=rpc_client,
        )
