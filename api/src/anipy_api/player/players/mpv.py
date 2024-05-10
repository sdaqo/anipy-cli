from typing import List, Optional
from anipy_api.player.base import SubProcessPlayerBase, PlayCallback


class Mpv(SubProcessPlayerBase):
    """The [mpv](https://mpv.io/) subprocess player class.
    For a controllable mpv look [here][anipy_api.player.players.mpv_control].

    Info:
        Not only mpv works but mpv forks like [mpv.net](https://github.com/mpvnet-player/mpv.net) also work.

    For detailed documentation about the functions and arguments have a look at the [base class][anipy_api.player.base.SubProcessPlayerBase].
    """

    def __init__(
        self,
        player_path: str,
        extra_args: List[str] = [],
        play_callback: Optional[PlayCallback] = None,
    ):
        """__init__ of Mpv

        Args:
            player_path:
            extra_args:
            play_callback:
        """
        self.player_args_template = [
            "{stream_url}",
            "--force-media-title={media_title}",
            "--force-window=immediate",
            *extra_args,
        ]

        super().__init__(
            player_path=player_path, extra_args=extra_args, play_callback=play_callback
        )
