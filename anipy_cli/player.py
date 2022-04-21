import os
import subprocess as sp
import time
from pypresence import Presence

from .history import history
from .misc import get_anime_info
from . import config


def mpv(entry, rpc_client=None):
    """
    Play a episode in mpv, a entry
    with all fields is required.
    It returns a subprocess instance,
    that for example can be killed like this:
    sub_proc.kill()
    """

    media_title = (
        entry.show_name + " - Episode: " + str(entry.ep) + " - " + str(entry.quality)
    )

    mpv_player_command = [
        f"{config.mpv_path}",
        f"--force-media-title={media_title}",
        f"--http-header-fields=Referer: {entry.embed_url}",
        "--force-window=immediate",
        f"{entry.stream_url}",
    ]
    for x in config.mpv_commandline_options:
        mpv_player_command.insert(3, x)

    if os.name in ("nt", "dos"):
        sub_proc = sp.Popen(mpv_player_command)
    else:
        sub_proc = sp.Popen(mpv_player_command, stdout=sp.PIPE, stderr=sp.DEVNULL)

    hist_class = history(entry)
    hist_class.write_hist()

    if config.dc_presence:
        dc_media_title = f"{entry.show_name} | {entry.ep}/{entry.latest_ep}"
        dc_presence(dc_media_title, entry.category_url, rpc_client)

    return sub_proc


def dc_presence_connect():
    CLIENT_ID = "966365883691855942"
    rpc_client = Presence(CLIENT_ID)
    rpc_client.connect()
    return rpc_client


def dc_presence(media_title, category_url, rpc_client):
    info = get_anime_info(category_url)
    rpc_client.update(
        details="Watching anime via anipy-cli",
        state=media_title,
        large_image=info["image_url"],
        small_image="https://github.com/Dankni95/ulauncher-anime/raw/master/images/icon.png",
        start=int(time.time()),
    )
