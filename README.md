# anipy-cli
### Little tool in python to watch anime from the terminal (the better way to watch anime)
### Has a resume playback function when  picking from History

### Scrapes: https://gogoanime.wiki

### Heavily inspired by https://github.com/pystardust/ani-cli/ (with more features)

[Still in development]

# Dependencies:

- `BeautifulSoup`

- `requests`

- `cURL`

- `mpv`


# Usage

### Install Dependencies

`pip install requests`

`pip install bs4`

Get mpv from: https://mpv.io/installation/

Curl should be preinstalled on Windows, Linux and macOS if not get it from here https://curl.se/download.html

## Start up 
To start `anipy-cli`

`pyton main.py`

## Options
### Set video quality
`main.py -q "Your desired quality"` 

By default `ani-py-cli` tries to get the best quality, you can spify a quality like `360/720/1080...` (without the "p" at the end)

You can also use  `best` or ` worst`.

### History
`main.py -H`

This will let you pick one of your anime-episodes that you previously watched and resumes playback at the time you exited the video player.


### Delete History

`main.py -D`

# Notes
## Resume PLayback
### The Resume playback function counts the seconds after video player is opened and stops when its closed. It stores the value and uses it when `-H` is called, not when you just play a episode like normal. When you play a episode from History, it will continue to count and adds it to the existing value.   