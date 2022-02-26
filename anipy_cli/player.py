import os
import subprocess as sp 

from .history import history

def mpv(entry):
    """
    Play a episode in mpv, a entry 
    with all fields is required.
    It returns a subprocess instance,
    that for example can be killed like this:
    sub_proc.kill()
    """
    
    media_titel = entry.show_name + " - EP: " + str(entry.ep)
                         
    mpv_player_command = [
                            "mpv", 
                            f'--force-media-title={media_titel}',
                            f'--http-header-fields=Referer: {entry.embed_url}',
                            f'{entry.stream_url}'
                         ]

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