from typing import List, Optional
from anipy_api.player.base import SubProcessPlayerBase, PlayCallback


class Iina(SubProcessPlayerBase):
    """The [iina](https://iina.io) subprocess player class.

    For detailed documentation about the functions and arguments have a look at the [base class][anipy_api.player.base.SubProcessPlayerBase].
    """

    def __init__(
        self,
        player_path: str,
        extra_args: List[str] = [],
        play_callback: Optional[PlayCallback] = None,
    ):
        """__init__ of Iina

        Args:
            player_path:
            extra_args:
            play_callback:
        """
        self.player_args_template = [
            "{stream_url}",
            "--mpv-force-media-title={media_title}",
            "--sub-files={subtitles}",
            "--referrer={referrer}",
            *extra_args,
        ]

        super().__init__(
            player_path=player_path, extra_args=extra_args, play_callback=play_callback
        )
