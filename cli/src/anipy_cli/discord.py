import functools
import time
from typing import TYPE_CHECKING

from pypresence import Presence

if TYPE_CHECKING:
    from anipy_api.anime import Anime
    from anipy_api.provider import ProviderStream


@functools.lru_cache(maxsize=None)
class DiscordPresence(object):
    def __init__(self):
        self.rpc_client = Presence(966365883691855942)
        self.rpc_client.connect()

    def dc_presence_callback(self, anime: "Anime", stream: "ProviderStream"):
        anime_info = anime.get_info()
        details_bytes = bytes(
            f"Watching via anipy-cli: {anime.name}".encode("utf-8", errors="ignore")
        )
        details = details_bytes[:128].decode("utf-8", errors="ignore")

        self.rpc_client.update(
            details=details,
            state=f"Episode {stream.episode}/{anime.get_episodes(stream.language)[-1]}",
            large_image=anime_info.image or "",
            small_image="https://raw.githubusercontent.com/sdaqo/anipy-cli/master/docs/assets/anipy-logo-dark-compact.png",
            large_text=anime.name,
            small_text="anipy-cli",
            start=int(time.time()),
            buttons=[
                {
                    "label": "Check out anipy-cli",
                    "url": "https://github.com/sdaqo/anipy-cli",
                }
            ],
        )
