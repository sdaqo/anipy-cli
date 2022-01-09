
![waving](https://capsule-render.vercel.app/api?type=waving&height=200&text=sdaqo/anipy-cli&fontAlign=60&fontAlignY=40&color=021224&fontColor=b0b8b2&animation=fadeIn)

### Little tool written in python to watch anime from the terminal (the better way to watch anime)
### Scrapes: https://gogoanime.wiki

### New: 
- Download functionality
- Config File
- Binge Mode

### Other versions:
- Ulauncher extension by @Dankni95: 
https://github.com/Dankni95/ulauncher-anime 

TODO:
- [x] 📺 Search gogoanime and extract video url to play anime 
- [x] ⌚History & resume playback 
- [x] ❇️Video-quality selection 
- [x] 🗒️Menu that pops up after starting episode 
- [x] 📥Download-function
- [x] ⚙ Config file for download-path and more
- [ ] 🚀Deploy to PyPI

[Still in development]

# Dependencies:
- `Python 3.0`

- `BeautifulSoup`

- `requests`

- `selenium`

- `Firefox/Chrome/Chromium`

- `cURL`

- `mpv`

- `tqdm`
 

# Usage

## Install Dependencies

#### [Note] If you are on Linux you can skip step 1. Just do `sudo make all` to install dependencies and be able execute the script everywhere. To uninstall just do `sudo make uninstall`
 
### 1. Python-Libs
To install `bs4`, `selenium`, `requests`, `webdriver-manager`, and `tqdm` open a terminal in the root-folder and execute `pip install -r requirements.txt`

### 2. Other dependencies

Get Python from: https://www.python.org/downloads/

Firefox, it's needed for Selenium, you can get it here: https://www.mozilla.org/firefox/new or with the package manager of your linux Distro.

Get mpv from: https://mpv.io/installation/

Curl should be preinstalled on Windows, Linux and macOS if not get it from here: https://curl.se/download.html

## Start up 
To start `anipy-cli` do:

`python3 main.py`

or, if you are on Linux and did `sudo make all` or `sudo make install` do:

`anipy-cli` from everywhere on your system.


## Options
### Set video quality
`main.py -q "Your desired quality"`  or `anipy-cli -q "Your desired quality"` 

By default `ani-py-cli` tries to get the best quality avalible. You can spify a quality like so: `360/720/1080...` (without the "p" at the end)

You can also use  `best` or ` worst`.

### Download

`main.py -d` or `anipy-cli -d`

This will drop you in the download mode, from ther you can search an anime and download it. You can specify a range of episodes like so `1-4` or `4-20` etc.

### History
`main.py -H` or `anipy-cli -H`

This will let you pick one of your anime-episodes that you previously watched and resumes playback at the time you exited the video player.

### Delete History

`main.py -D` or `anipy-cli -D`

### Binge Mode

`main.py -b` or `anipy-cli -b`

Specify a range of episodes and play them back to back.

### Config File
Change `config.py` if you want any of the options given there changed.

# Features
### Resume Playback
#### The Resume playback function counts the seconds after the video player is opened and stops when its closed (does not stop when you pause the video). It stores the value and uses it when `-H` is called, not when you just play a episode like normal. When you play a episode from History, it will continue to count and adds it to the existing value.    

### Menu
#### Has a menu that pops up after you picked an episode to play, there yopu can either play next episode, play previous episode, replay episode, open history selection, search for another anime or quit.

# Credits
#### Heavily inspired by https://github.com/pystardust/ani-cli/
#### Migueldeoleiros for the makefile 
