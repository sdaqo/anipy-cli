import os
import time
import sys
import subprocess as sp
from pypresence import Presence
from pypresence.exceptions import DiscordNotFound


from .history import history
from .misc import get_anime_info, error
from .colors import colors
from .config import Config


def start_player(entry, rpc_client=None, player=None):
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

    if not player:
        player = Config().player_path

    if player in ("mpv", "syncplay", "mpvnet"):

        player_command = [
            f"{player}",
            f"{entry.stream_url}",
             "--" if player == "syncplay" else "",
            f"--force-media-title={media_title}",
            f"--referrer={entry.embed_url}",
             "--force-window=immediate",
        ]

        for x in Config().mpv_commandline_options:
            player_command.insert(3, x)

    elif player == "vlc" or Config().player_path == "vlc":

        player_command = [
            f"{player}",
            f"--http-referrer='{entry.embed_url}'",
            f"--meta-title='{media_title}'",
            f"{entry.stream_url}",
        ]

        for x in Config().vlc_commandline_options:
            player_command.insert(3, x)

    else:
        error("Specified player is unknown")
        sys.exit()

    try:
        if os.name in ("nt", "dos"):
            sub_proc = sp.Popen(player_command)
        else:
            sub_proc = sp.Popen(player_command, stdout=sp.PIPE, stderr=sp.DEVNULL)
    except FileNotFoundError as e:
        print(colors.RED + "Error:", e, colors.END)
        sys.exit()

    hist_class = history(entry)
    hist_class.write_hist()

    if rpc_client:
        dc_media_title = f"{entry.show_name} | {entry.ep}/{entry.latest_ep}"
        dc_presence(dc_media_title, entry.category_url, rpc_client)

    return sub_proc

def create_mpv_controllable():
    import mpv
    player = mpv.MPV(
        input_default_bindings=True,
        input_vo_keyboard=True,
        force_window="immediate",
        osc=True
    )

    return player

def mpv_start_stream(entry, player, rpc_client=None):
    media_title = (
        entry.show_name + " - Episode: " + str(entry.ep) + " - " + str(entry.quality)
    )

    player.referrer = entry.embed_url
    player.force_media_title = media_title
    player.play(entry.stream_url)

    hist_class = history(entry)
    hist_class.write_hist()

    if Config().dc_presence:
        dc_media_title = f"{entry.show_name} | {entry.ep}/{entry.latest_ep}"
        dc_presence(dc_media_title, entry.category_url, rpc_client)

    return player

def dc_presence_connect():
    CLIENT_ID = 966365883691855942
    rpc_client = None
    try:
        rpc_client = Presence(CLIENT_ID)
        rpc_client.connect()
        print(colors.GREEN + "Initalized Discord Presence Client" + colors.END)
    except DiscordNotFound:
        print(
            colors.RED
            + "Discord is not opened, can't initialize Discord Presence"
            + colors.END
        )

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


# backwards-compatability
#mpv = start_player
