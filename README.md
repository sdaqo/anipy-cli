> # Playback in local video player currently not working due to changes on gogoplay, trying to fix this.

# anipy-cli
### Little tool written in python to watch anime from the terminal (the better way to watch anime)
### Scrapes: https://gogoanime.wiki

TODO:
- [x] 📺 Search gogoanime and extract .m3u8 link to play anime 
- [x] ⌚History & resume playback 
- [x] ❇️Video-quality selection 
- [x] 🗒️Menu that pops up after starting episode 
- [ ] 👇Download-function
- [ ] 🚀Deploy to PyPI

[Still in development]

# Dependencies:
- `Python 3.0`

- `BeautifulSoup`

- `requests`

- `cURL`

- `mpv`
 

# Usage

### Install Dependencies
Get Python from: https://www.python.org/downloads/



Get mpv from: https://mpv.io/installation/

Curl should be preinstalled on Windows, Linux and macOS if not get it from here: https://curl.se/download.html

 To install requests do: `pip install requests`

To install BeautifulSoup do: `pip install bs4`

## Start up 
To start `anipy-cli`

`pyton main.py`

## Options
### Set video quality
`main.py -q "Your desired quality"` 

By default `ani-py-cli` tries to get the best quality avalible. You can spify a quality like so: `360/720/1080...` (without the "p" at the end)

You can also use  `best` or ` worst`.

### History
`main.py -H`

This will let you pick one of your anime-episodes that you previously watched and resumes playback at the time you exited the video player.


### Delete History

`main.py -D`

# Features
### Resume Playback
#### The Resume playback function counts the seconds after the video player is opened and stops when its closed (does not stop when you pause the video). It stores the value and uses it when `-H` is called, not when you just play a episode like normal. When you play a episode from History, it will continue to count and adds it to the existing value.    

### Menu
#### Has a menu that pops up after you picked an episode to play, there yopu can either play next episode, play previous episode, replay episode, open history selection, search for another anime or quit.

# Credits
### Heavily inspired by https://github.com/pystardust/ani-cli/
