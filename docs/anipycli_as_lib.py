"""
Examples to use
anipy-cli as library.
More descriptions can be
found by the functions/classes itself.
"""
# Don't run this file, it won't work, it is only for demonstration purposes

import anipy_cli

"""ENTRY"""
# A class that saves metadata, it is
# needed for almost every function.
# It is like a struct from C.
# It looks like this:
#    class Entry:
#        show_name: str = "" # name of show
#        category_url: str = "" # category url of show
#        ep_url: str = "" # ep url with episode corresponding to ep
#        embed_url: str = "" # embed url of ep_url
#        stream_url: str = "" # m3u8/mp4 link of embed_url
#        ep: int = 0 # episode currently played/downloaded or whatever
#        latest_ep: int = 0 # latest episode of the show
#        quality: str = "" # current quality
entry = anipy_cli.Entry()


"""QUERY"""

# Get results from a query, it takes
# a search parameter and an empty entry.
query_class = anipy_cli.query("naruto", entry)
# query.get_links() returns a tuple with a
# list of links and names: (self.links, self.names)
# The links are not complete (/category/naruto),
# you will have to prepend the gogoanime url to it.
links_and_names = query_class.get_links()
print(links_and_names[0])  # prints links
print(links_and_names[1])  # prints names

"""EPISODE HANDLING"""

# Episode Handling is done with
# epHandler, it can get the latest
# episode, generate episode links,
# get next episode and previous episode.
# it requires the fields category_url,
# and ep.
ep_class = anipy_cli.epHandler(entry)
# get latest episode
latest_ep = ep_class.get_latest()
# generate ep link, returns an entry
entry = ep_class.gen_eplink()
# get next episode, returns an entry
next_ep = ep_class.next_ep()
# get prev episode, returns an entry
prev_ep = ep_class.prev_ep()
# get your entry back
entry = ep_class.get_entry()

"""VIDEO-URL"""

# Extracting the video and emebed url is
# done with the videourl class, it takes an entry
# that has to at least have ep_url filled.
# It also takes a quality argument which can have
# the standard qualities (1080, 720 etc.) or worst/best as value.
url_class = anipy_cli.videourl(entry, "best")
# generate stream url (this also, automatically generates the embed url)
url_class.stream_url()
# get your entry back filled with stream and embed url fields
entry = url_class.get_entry()

"""DOWNLOAD"""

# Download a m3u8/mp4 link:
# this class requires all
# fields of entry to be filled.
# It also requires a quality argument
# in the same form as anipy_cli.videourl.
# You can also enable ffmpeg download
# for m3u8 playlists with `ffmpeg=True`,
# though this is not recommended, only
# use it when internal downloader fails,
# also note that there is an option in
# config.py for it.
dl_class = anipy_cli.download(entry, "worst", ffmpeg=True)
# downloads a m3u8 or a mp4 link
dl_class.download()

"""PLAYER"""

# Every Player has its own class, to get the default
# player class use this:
player = anipy_cli.player.get_player(player_override="mpv")
# The default player is specified in the config, but you can
# also use player_override="..." to override the default player

# All players have common methods:

# Play title from an Entry class
player.play_title(entry)

# Play a file from a specific path
player.play_file(path)

# Wait until thplayback finishes/player is closed
player.wait()

# Kill the player
player.kill_player()


# You can also, instead of using the get_player function,
# use the player classes directly:

vlc_player = anipy_cli.player.players.Vlc()

# This is a controllable mpv player, it has the same common methods
# as the other players but is a little special as you can completely
# control the player. Read more about what you can do with it here:
# https://github.com/jaseg/python-mpv
contr_mpv_player = anipy_cli.player.players.MpvControllable()


"""HISTORY"""

# Read the save data from the history.json file
# history class: history.history(entry)
history_class = anipy_cli.history(entry)
save_data = history_class.read_save_data()
# Writing to history file:
# Following entry fields are required
# for writing to history file:
#        - show_name
#        - category_url
#        - ep_url
#        - ep
history_class.write_hist()

"""ANIME-INFO"""

# Get some metadata about an anime,
# it takes a category url
anipy_cli.get_anime_info("https://gogoanime.gg/category/hyouka")
# It returns a dict with the image-url,
# type of the anime, the synopsis,
# a list with the genres, the release year and
# the status of the anime.

"""CONFIG"""

# The config file can be
# easily used, it just saves
# some variables, that can be used.
# Examples:
dl_folder = anipy_cli.config.config.download_folder_path
mpv_cmd_opts = anipy_cli.config.config.mpv_commandline_options
# More can be found in config.py directly

"""Seasonal"""

# The seasonal Class can fetch latest episodes
# from animes specified in the user_data/seasonals.json
# file (or the file specified in the config).
# You can also add, delete or update a show in
# seasonals.json, listing all shows is also
# possible.

# Create the class
seasonal_class = anipy_cli.Seasonal()
# Fetch latest episodes, this function returns
# a dictionary with the episodes, it looks like
# this:
#           {"name": {
#               "ep_list": [[ep, ep-link], [], ...],
#               "category_url": "https://..."
#               },
#            "another anime": {
#                ...
#               },
#           }
seasonal_class.latest_eps()
# Add a show to seasonals.json, this
# takes a name, a category_url and the
# start episode as parameter
seasonal_class.add_show("Hyouka", "https://gogoanime.gg/category/hyouka", "3")
# Delete a show from seasonals.json,
# this takes the name of the show as parameter
seasonal_class.del_show("Hyouka")
# List all shows in seasonals.json,
# with their respective episodes.
seasonal_class.list_seasonals()
# Returns a 2D list like this:
# [["Hyouka", "3"], ["Another Anime", "2"]]


# This is it for now, maybe this will be extended.
