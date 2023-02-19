"""
 █████  ███    ██ ██ ██████  ██    ██       ██████ ██      ██ 
██   ██ ████   ██ ██ ██   ██  ██  ██       ██      ██      ██ 
███████ ██ ██  ██ ██ ██████    ████  █████ ██      ██      ██ 
██   ██ ██  ██ ██ ██ ██         ██         ██      ██      ██ 
██   ██ ██   ████ ██ ██         ██          ██████ ███████ ██ 

~ The best tool to watch and Download your favourite anime.

https://github.com/sdaqo/anipy-cli

"""
from anipy_cli.download import download
from anipy_cli.url_handler import epHandler, videourl
from anipy_cli import config
from anipy_cli.query import query
from anipy_cli.player import get_player
from anipy_cli.misc import Entry, get_anime_info
from anipy_cli.seasonal import Seasonal
from anipy_cli.history import history
