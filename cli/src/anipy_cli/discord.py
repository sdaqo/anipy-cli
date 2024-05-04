import time
from typing import TYPE_CHECKING
from py_singleton import singleton

from pypresence import Presence

if TYPE_CHECKING:
    from anipy_api.provider import ProviderInfoResult

@singleton
class DiscordPresence(object):
    def  __init__(self):
        self.rpc_client = Presence(966365883691855942)
        self.rpc_client.connect()

    def dc_presence_callback(
       self, media_title: str, anime_info: "ProviderInfoResult"
    ):
        self.rpc_client.update(
            details="Watching anime via anipy-cli",
            state=media_title,
            large_image=anime_info.image or "",
            small_image="https://github.com/Dankni95/ulauncher-anime/raw/master/images/icon.png",
            start=int(time.time()),
        )
