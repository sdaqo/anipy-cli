import os
import sys
from dataclasses import dataclass

from .colors import colors

options = [
    colors.GREEN + "[n] " + colors.END + "Next Episode",
    colors.GREEN + "[p] " + colors.END + "Previous Episode",
    colors.GREEN + "[r] " + colors.END + "Replay episode",
    colors.GREEN + "[s] " + colors.END + "Select episode",
    colors.GREEN + "[h] " + colors.END + "History selection",
    colors.GREEN + "[a] " + colors.END + "Search for Anime",
    colors.GREEN + "[q] " + colors.END + "Quit"
]


@dataclass
class entry:
    """
    This is the class that saves
    metadata about a show. It is required
    by all classes, it is a essential
    part of this script.
    """
    show_name: str = ""
    category_url: str = ""
    ep_url: str = ""
    embed_url: str = ""
    stream_url: str = ""
    ep: int = 0
    latest_ep: int = 0
    quality: str = ""

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def error(error: str) -> None:
    """ 
    Error function for better error handling,
    that takes an error and prints it to stderr.
    """
    sys.stderr.write(
        colors.ERROR + "anipy-cli: error: " + error + colors.END + '\n')
    
def response_err(req, link) -> None:
    """ 
    Function that checks if a requsted
    was succesfull.
    """
    if req.ok:
        pass
    else:
        error(f"requsted url not avalible/blocked: {link}: response-code: {req.status_code}")
        sys.exit()

def loc_err(soup, link: str, element: str) -> None:
    """ 
    Function that checks if beautifulsoup
    could locate a element.
    """
    if soup == None:
        error(f"could not locate {element}: {link}")
        sys.exit()

def keyboard_inter() -> None:
    print(colors.ERROR + "\nanipy-cli: error: interrupted")
    sys.exit()
