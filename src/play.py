# local imports
from src.history import write_history
import config
#imports
from threading import Thread
import subprocess as sp
import time
import os

terminate = False


def play(embed_url, video_url, link, is_history, start_at="0"):
    global stop, sub_proc
    stop = False

    video_player_command = [
    config.mpv_path 
    + f" --force-media-title={link.replace(config.gogoanime_url, '')} " 
    + f"{'--start=+' + str(start_at)  if config.mpv_resume_episode else ''}"  
    + f'--http-header-fields="Referer: {embed_url}" ' 
    + config.mpv_commandline_options + f" '{video_url}'"
    ]

    Thread(target=write_history, args=(link, is_history)).start()
    if os.name in ('nt', 'dos'):
        sub_proc = sp.Popen(video_player_command)
    else:
        sub_proc = sp.Popen(video_player_command,
                            stdout=sp.PIPE,
                            shell=True,
                            preexec_fn=os.setsid,
                            stderr=sp.DEVNULL)

    # check if sub_proc process is running, if not break out of loop
    while True:
        poll = sub_proc.poll()
        if poll is None:
            pass
        else:
            break

        time.sleep(0.5)

    stop = True  # this stops write_history function in history.py
