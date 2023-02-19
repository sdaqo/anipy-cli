from anipy_cli.player.players.base import SubProcessPlayerBase
from anipy_cli.config import Config


class Mpv(SubProcessPlayerBase):
    def __init__(self, rpc_client=None, mpv_exec_name: str="mpv"):
        player_args_template = [
            "{stream_url}",
            "--force-media-title={media_title}",
            "--referrer={embed_url}",
            "--force-window=immediate",
            *Config().mpv_commandline_options
        ]

        super().__init__(
            player_args_template=player_args_template,
            rpc_client=rpc_client,
            player_exec=mpv_exec_name
        )
