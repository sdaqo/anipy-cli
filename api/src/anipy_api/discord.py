import time
from typing import TYPE_CHECKING, Optional

from pypresence import Presence

if TYPE_CHECKING:
    from anipy_api.provider import ProviderInfoResult


def dc_presence_connect() -> Presence:
    rpc_client = Presence(966365883691855942)
    rpc_client.connect()

    return rpc_client


def dc_presence(
    media_title: str, anime_info: "ProviderInfoResult", rpc_client: Presence
):
    rpc_client.update(
        details="Watching anime via anipy-cli",
        state=media_title,
        large_image=anime_info.image or "",
        small_image="https://github.com/Dankni95/ulauncher-anime/raw/master/images/icon.png",
        start=int(time.time()),
    )
