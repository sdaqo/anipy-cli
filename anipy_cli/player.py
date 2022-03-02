import os
import subprocess as sp 

from .history import history
from . import config

def mpv(entry):
    """
    Play a episode in mpv, a entry 
    with all fields is required.
    It returns a subprocess instance,
    that for example can be killed like this:
    sub_proc.kill()
    """
    
    media_title = entry.show_name + " - EP: " + str(entry.ep) + " - " + str(entry.quality)

                         
    mpv_player_command = [
                            f'{config.mpv_path}', 
                            f'--force-media-title={media_title}',
                            f'--http-header-fields=Referer: {entry.embed_url}',
                            f'{entry.stream_url}'
                         ]
    for x in config.mpv_commandline_options: 
        mpv_player_command.insert(3, x)

    if os.name in ('nt', 'dos'):
        sub_proc = sp.Popen(mpv_player_command)
    else:
        sub_proc = sp.Popen(
                    mpv_player_command,
                    stdout=sp.PIPE,
                    stderr=sp.DEVNULL)       
    
    hist_class = history(entry)
    hist_class.write_hist()

    return sub_proc
