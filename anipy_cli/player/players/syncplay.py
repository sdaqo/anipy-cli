from anipy_cli.player.players.base import SubProcessPlayerBase
from anipy_cli.config import Config


class Syncplay(SubProcessPlayerBase):
    def __init__(self, player_path: str, rpc_client=None):
        self.player_exec = "syncplay"
        player_args_template = [
            "--" "--http-referrer='{embed_url}'",
            "--meta-title='{media_title}'",
            "{stream_url}",
            *Config().mpv_commandline_options,
        ]

        super().__init__(
            rpc_client=rpc_client,
            player_path=player_path,
            player_args_template=player_args_template,
        )
