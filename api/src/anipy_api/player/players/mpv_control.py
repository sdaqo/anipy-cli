import mpv
from typing import TYPE_CHECKING

from anipy_api.player.base import PlayerBase

if TYPE_CHECKING:
    from anipy_api.provider import ProviderStream
    from anipy_api.anime import Anime


class MpvControllable(mpv.MPV, PlayerBase):
    def __init__(self, rpc_client=None):
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
