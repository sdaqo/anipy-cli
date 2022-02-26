
![waving](https://capsule-render.vercel.app/api?type=waving&height=200&text=sdaqo/anipy-cli&fontAlign=60&fontAlignY=40&color=021224&fontColor=b0b8b2&animation=fadeIn)

> ## Anipy-cli now fresh and new: anipy-cli 2.0!

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

### Notes:
For now some (not a lot) shows's stream url is  not able
to be fetched because they are played
from the streamsb server (e.g. sangatsu no lion)
which has dirty javascript to avoid scraping.
No patch for this is implemented yet.


# Dependencies:
- `Python 3.10`

- `mpv`

- `BeautifulSoup`

- `requests`


# Installation

### For normal usage

#### Linux:

- `sudo make all` to install dependencies and anipy-cli
- `sudo make install` to install anipy-cli
- `sudo make uninstall` to uninstall anipy-cli

To run just do `anipy-cli` 

#### Windows:

The windows installer is somewhat unstable so please open an issue when errors occur.

To install:
- Start a CMD session as administrator
- CD in the win folder of anipy-cli
- Type `win-installer.bat`
- It will now install python libs, create a bin folder in the root directory of anipy-cli that contains a anipy-cli.bat file and set a entry to the system path variable.
- You may have to reboot your PC before going to the next step.
- Now open a new cmd (if you want color support get windows terminal from microsoft store) and type `anipy-cli`

To uninstall:
- Start a CMD session as administrator
- CD in the win folder of anipy-cli
- Type `win-uninstaller.bat`
- It will now delete the bin folder, but it will NOT delte the entry to the path variable, you should delete that yourself.

### For libary usage

For "documentation", in the docs folder is a `anipycli_as_lib.py` file. You can also directly look at the source code, most function have comments.
- In the root directory do `python setup.py bdist_wheel`
- A dist folder with a wheel file got created, go into it.
- In the dist folder run `pip install file.whl`

#### Important:
To import the libary dont import `anipy-cli`, but `anipy_cli` (no '-' is allowed)

# Usage
To start `anipy-cli` do:

`python3 anipy-cli.py` (Note that all options down below have to also be run with this command)

or

`anipy-cli` (if anipy-cli was installed trough an installer)


## Options
### Set video quality
`anipy-cli -q "Your desired quality"` or `anipy-cli -q "Your desired quality"`

By default `ani-py-cli` tries to get the best quality avalible. You can spify a quality like so: `360/720/1080...` (without the "p" at the end)

You can also use  `best` or ` worst`.

### Download

`anipy-cli -d`

This will drop you in the download mode, from ther you can search an anime and download it. You can specify a range of episodes like so `1-4` or `4-20` etc.

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
#### Migueldeoleiros for the makefile 
