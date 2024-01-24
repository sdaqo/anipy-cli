import mpv

from anipy_cli.player.players.base import PlayerBase


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

    def play_title(self, entry):
        self.force_media_title = self._get_media_title(entry)

        self.referrer = entry.embed_url
        self.play(entry.stream_url)

        self._write_hist(entry)
        self._start_dc_presence(entry)

    def play_file(self, path: str):
        self.play(path)

    def wait(self):
        self.wait_for_playback()

    def kill_player(self):
        self.terminate()
