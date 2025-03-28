from typing import List, Optional
from anipy_api.player.base import SubProcessPlayerBase, PlayCallback


class Syncplay(SubProcessPlayerBase):
    """The [syncplay](https://syncplay.pl) subprocess player class.

    For detailed documentation about the functions and arguments have a look at the [base class][anipy_api.player.base.SubProcessPlayerBase].
    """

    def __init__(
        self,
        player_path: str,
        extra_args: List[str] = [],
        play_callback: Optional[PlayCallback] = None,
    ):
        """__init__ of Syncplay

        Args:
            player_path:
            extra_args:
            play_callback:
        """
        self.player_args_template = [
            "--",
            "--meta-title='{media_title}'",
            "--sub-files={subtitles}",
            "--referrer={referrer}" "{stream_url}",
            *extra_args,
        ]

        super().__init__(
            player_path=player_path, extra_args=extra_args, play_callback=play_callback
        )
