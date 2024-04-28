from typing import List
from anipy_api.player.base import SubProcessPlayerBase


class Syncplay(SubProcessPlayerBase):
    """The [syncplay](https://syncplay.pl) subprocess player class.

    For detailed documentation have a look at the [base class][anipy_api.player.base.SubProcessPlayerBase].
    """
    def __init__(self, player_path: str, extra_args: List[str] = [], rpc_client=None):
        self.player_args_template = [
            "--",
            "--meta-title='{media_title}'",
            "{stream_url}",
            *extra_args,
        ]

        super().__init__(
            rpc_client=rpc_client,
            player_path=player_path,
            extra_args=extra_args
        )
