from threading import Thread
import subprocess as sp
from  src.history import write_history

player = "mpv"


def play(embed_url, video_url, link, is_history, start_at="0"):
    global stop 
    stop = False
    player_command = player + " --start=+" + str(start_at) + " --cache=yes " +  '--http-header-fields="Referer: ' + embed_url + '"' + " " + video_url
    Thread(target=write_history, args=(link, is_history)).start()
    sp.run(player_command, 
           shell=True, 
           stdout=sp.DEVNULL, 
           stderr=sp.STDOUT)
    stop = True


