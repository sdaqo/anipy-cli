from typing import TYPE_CHECKING, Any, Optional

from anipy_api.player.base import PlayCallback, PlayerBase

if TYPE_CHECKING:
    from anipy_api.provider import ProviderStream
    from anipy_api.anime import Anime


class MpvControllable(PlayerBase):
    """This player can be controlled and it also does not close if
    the media is changed, the window stays open until `kill_player` is called.
    You need libmpv for this, check the [python-mpv](https://github.com/jaseg/python-mpv?tab=readme-ov-file#requirements)
    project's requirements to know where to get it.

    For detailed documentation about the functions have a look at the [base class][anipy_api.player.base.PlayerBase].

    If you want to use the extra features of the controllable player look
    [here](https://github.com/jaseg/python-mpv?tab=readme-ov-file#usage)
    for documentation (or use your LSP), the python-mpv mpv instance lives in the mpv attribute.

    Attributes:
        mpv: The python-mpv mpv instance
    """

    def __init__(
        self, play_callback: Optional[PlayCallback] = None, **mpv_args: Optional[Any]
    ):
        """__init__ of MpvControllable

        Args:
            play_callback: Callback called upon starting to play a title with `play_title`
            **mpv_args: Arguments passed to the MPV instance check the [python-mpv repo](https://github.com/jaseg/python-mpv?tab=readme-ov-file#usage)
                or check the [official list of arguments](https://mpv.io/manual/master/#properties). There are some default arguments set, if you specify
                any arguments here, all the defaults will be discarded and this will be used instead.
        """
        super().__init__(play_callback=play_callback)

        # I know this is a crime, but pytohn-mpv loads the so/dll on import and this will break all the stuff for people that do not have that.
        from mpv import MPV

        if len(mpv_args) <= 1:
            mpv_args = {
                "input_default_bindings": True,
                "input_vo_keyboard": True,
                "force_window": "immediate",
                "title": "MPV - Receiving Links from anipy-cli",
                "osc": True,
            }

        self.mpv = MPV(**mpv_args)

    def play_title(self, anime: "Anime", stream: "ProviderStream"):
        self.mpv.force_media_title = self._get_media_title(anime, stream)

        self.mpv.play(stream.url)

        self._call_play_callback(anime, stream)

    def play_file(self, path: str):
        self.mpv.play(path)

    def wait(self):
        self.mpv.wait_for_playback()

    def kill_player(self):
        self.mpv.terminate()
