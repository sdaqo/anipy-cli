
![waving](https://capsule-render.vercel.app/api?type=waving&height=200&text=sdaqo/anipy-cli&fontAlign=60&fontAlignY=40&color=021224&fontColor=b0b8b2&animation=fadeIn)

> ## Anipy-cli now new and improved: anipy-cli 2.0!

### Little tool written in python to watch anime from the terminal (the better way to watch anime)
### Scrapes: https://gogoanime.wiki


### Other versions:
- Ulauncher extension by @Dankni95: 
https://github.com/Dankni95/ulauncher-anime 

# 2.0 Updates
- Complete rewrite
- Can now also be used as libary
- Way Faster
- Less dependencies
- Seasonal and binge mode are
  not yet implemented
- No more Spagehtti code

# Dependencies:
- `Python 3`

- `mpv`

- `BeautifulSoup`

- `requests`


# Installation

Recommended installation:

`python3 -m pip install git+https://github.com/sdaqo/anipy-cli`

Other methodes can be found in docs/install.md

## For libary usage

Use the recommended installation

### Important:
To import the libary dont import `anipy-cli`, but `anipy_cli` (no '-' is allowed)



## Other Dependencies

#### MPV
For mpv installation look here: https://mpv.io/installation/


    
# Usage

### Set video quality
`anipy-cli -q "Your desired quality"`

By default `anipy-cli` tries to get the best quality avalible. You can specify a quality like so: `360/720/1080...` (without the "p" at the end)

You can also use `best` or ` worst`.

### Download

`anipy-cli -d`

This will drop you in the download mode, from there you can search for an anime and download it. You can specify a range of episodes like so `1-4` or `4-20` etc.

### History

`anipy-cli -H`

This will let you pick one of your anime-episodes that you previously watched and resumes playback at the time you exited the video player.

### Delete History

`anipy-cli -D`

You can change your history.txt path in `config.py`

### Binge Mode (not implemented look at 2.0 Updates)

`anipy-cli -b`

Specify a range of episodes and play them back to back.

### Seasonal Anime Mode (not implemented look at 2.0 Updates)

`anipy-cli -s`

Binge-watch or bulk-download the newest episodes of animes.

You can change your seasonals.txt path in `config.py`

### Config File

You can get the path to your config file with `anipy-cli -c`

Change `config.py` if you want any of the options given there changed.

# Features

### Big range of Modes

- Download
- Binge (not implemented look at 2.0 Updates)
- Seasonal (not implemented look at 2.0 Updates)

### Resume Playback
Resume playback is deprecated. Use https://github.com/AN3223/dotfiles/blob/master/.config/mpv/scripts/auto-save-state.lua (from https://github.com/mpv-player/mpv/wiki/User-Scripts) for mpv, this is way more reliable than the old function.

### Menu
#### Has a menu that pops up after you picked an episode to play, there yopu can either play next episode, play previous episode, replay episode, open history selection, search for another anime or quit.

# Credits
#### Heavily inspired by https://github.com/pystardust/ani-cli/
#### [Migueldeoleiros](https://github.com/migueldeoleiros) and [Dabbing-Guy](https://github.com/Dabbing-Guy) for the makefile 
#### All contributors for contributing
