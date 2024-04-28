import mpv
from typing import TYPE_CHECKING

from anipy_api.player.base import PlayerBase

if TYPE_CHECKING:
    from anipy_api.provider import ProviderStream
    from anipy_api.anime import Anime


class MpvControllable(mpv.MPV, PlayerBase):
    """This player can be controlled and it also does not close if 
    the media is changed, the window stays open until `kill_player` is called.

    For detailed documentation have a look at the [base class][anipy_api.player.base.PlayerBase].

    If you want to use the extra features of the controllable player look 
    [here](https://github.com/jaseg/python-mpv?tab=readme-ov-file#usage)
    for documentation (or use your LSP). 
    """
    def __init__(self, rpc_client=None):
        """__init__ of MpvControllable

        Args:
            rpc_client: Discord RPC client
        """
        super().__init__(
            input_default_bindings=True,
            input_vo_keyboard=True,
            force_window="immediate",
            title="MPV - Receiving Links from anipy-cli",
            osc=True,
        )
        self._rpc_client = rpc_client

    @property
    def rpc_client(self):
        return self._rpc_client

    def play_title(self, anime: "Anime", stream: "ProviderStream"):
        self.force_media_title = self._get_media_title(anime, stream)

        self.play(stream.url)

        self._start_dc_presence(anime, stream)

    def play_file(self, path: str):
        self.play(path)

    def wait(self):
        self.wait_for_playback()

    def kill_player(self):
        self.terminate()
