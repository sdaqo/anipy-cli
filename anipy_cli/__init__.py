"""
 █████  ███    ██ ██ ██████  ██    ██       ██████ ██      ██ 
██   ██ ████   ██ ██ ██   ██  ██  ██       ██      ██      ██ 
███████ ██ ██  ██ ██ ██████    ████  █████ ██      ██      ██ 
██   ██ ██  ██ ██ ██ ██         ██         ██      ██      ██ 
██   ██ ██   ████ ██ ██         ██          ██████ ███████ ██ 

~ The best tool to watch and Download your favourite anime.

https://github.com/sdaqo/anipy-cli

"""
from .download import download
from .url_handler import epHandler, videourl
from . import config
from .query import query
from .player import get_player
from .misc import Entry, get_anime_info
from .seasonal import Seasonal
from .history import history

