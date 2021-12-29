# local imports
from  src.history import write_history
#imports
from threading import Thread
import subprocess as sp
import time
import os

player = "mpv"
terminate = False
base_url = "https://gogoanime.wiki/"

def play(embed_url, video_url, link, is_history, start_at="0"):
    global stop, sub_proc
    stop = False
    player_command = player + f" --force-media-title={link.replace(base_url, '')} " + f" --start=+{str(start_at)}" + " --cache=yes " +  f'--http-header-fields="Referer: {embed_url}" ' + f"'{video_url}'"
    Thread(target=write_history, args=(link, is_history)).start()
    if os.name in ('nt', 'dos'):
        sub_proc = sp.Popen(player_command)
    else:
        sub_proc = sp.Popen(player_command, 
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
        
    stop = True # this stops write_history function in history.py

