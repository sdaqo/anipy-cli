from anipy_cli.player.players.base import SubProcessPlayerBase
from anipy_cli.config import Config


class Vlc(SubProcessPlayerBase):
    def __init__(self, player_path: str, rpc_client=None):
        player_args_template = [
            "--http-referrer='{embed_url}'",
            "--meta-title='{media_title}'",
            "{stream_url}",
            *Config().vlc_commandline_options,
        ]

        super().__init__(
            rpc_client=rpc_client,
            player_path=player_path,
            player_args_template=player_args_template,
        )
