![waving](https://capsule-render.vercel.app/api?type=waving&height=200&text=sdaqo/anipy-cli&fontAlign=60&fontAlignY=40&color=021224&fontColor=b0b8b2&animation=fadeIn)

https://user-images.githubusercontent.com/63876564/162056019-ed0e7a60-78f6-4a2c-bc73-9be5dc2a4f07.mp4

### Little tool written in python to watch and download anime from the terminal (the better way to watch anime), also applicable as an API.

### Scrapes: https://gogoanime.gg

#### If you dont like to use a cli there is a GUI and other versions [here](#other-versions).

# Contents

- [Installation](#Installation)
- [Usage](#Usage)
- [Libary Usage](#libary-usage)
- [What it can do](#what-it-can-do)
- [Other Versions](#other-versions)
- [Credits](#Credits)

# Installation

<a href="https://pypi.org/project/anipy-cli/">![PyPI](https://img.shields.io/pypi/v/anipy-cli?style=for-the-badge)</a>

Recommended installation:

`python3 -m pip install anipy-cli --upgrade`

Directly from the repo (may be newer):

`python3 -m pip install git+https://github.com/sdaqo/anipy-cli`

For video playback mpv is needed. Get it here: https://mpv.io/installation/

If you would like to use another video player, you will need to specify its path in the config file.

Optionally, you can install [ffmpeg](https://ffmpeg.org/download.html) to download m3u8 playlists instead of using the internal downloader. You can use it with the `-f` flag. This is something you should use if the internal downlaoder fails since ffmpeg is comparatively slow.

### Config

When you start the program for the first time the config file gets created automatically

Places of the config:

- Linux: ~/.config/anipy-cli/config.yaml
- Windows: %USERPROFILE%/AppData/Local/anipy-cli/config.yaml
- MacOS: ~/.config/anipy-cli/config.yaml

[Sample Config](https://github.com/sdaqo/anipy-cli/blob/master/docs/sample_config.yaml)

**Attention Windows Users Using MPV:** If you activate the option `reuse_mpv_window`, you will have to download and put the `mpv-2.dll` in your path. To get it go look here: https://sourceforge.net/projects/mpv-player-windows/files/libmpv/

**Attention Windows Users on Config File Placement:** If you have downloaded Python from the Microsoft Store, your config file will be cached inside of your Python's AppData. For example: `%USERPROFILE%\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.11_qbz5n2kfra8p0\LocalCache\Local\anipy-cli\config.yaml`.

# Usage

```
usage: anipy-cli [-D | -B | -H | -S | -M | --delete-history] [-q QUALITY] [-f] [-o] [-a] [-p {mpv,vlc,syncplay,mpvnet}] [-l LOCATION] [--mal-password MAL_PASSWORD] [-h] [-v] [--config-path]

Play Animes from gogoanime in local video-player or Download them.

Actions:
  Different Actions and Modes of anipy-cli (only pick one)

  -D, --download        Download mode. Download multiple episodes like so: first_number-second_number (e.g. 1-3)
  -B, --binge           Binge mode. Binge multiple episodes like so: first_number-second_number (e.g. 1-3)
  -H, --history         Show your history of watched anime
  -S, --seasonal        Seasonal Anime mode. Bulk download or binge watch newest episodes.
  -M, --my-anime-list   MyAnimeList mode. Similar to seasonal mode, but using MyAnimeList (requires MAL account credentials to be set in config).
  --delete-history      Delete your History.

Options:
  Options to change the behaviour of anipy-cli

  -q QUALITY, --quality QUALITY
                        Change the quality of the video, accepts: best, worst or 360, 480, 720 etc. Default: best
  -f, --ffmpeg          Use ffmpeg to download m3u8 playlists, may be more stable but is way slower than internal downloader
  -o, --no-seas-search  Turn off search in season. Disables prompting if GoGoAnime is to be searched for anime in specific season.
  -a, --auto-update     Automatically update and download all Anime in seasonals list from start EP to newest.
  -p {mpv,vlc,syncplay,mpvnet}, --optional-player {mpv,vlc,syncplay,mpvnet}
                        Override the player set in the config.
  -l LOCATION, --location LOCATION
                        Override all configured download locations
  --mal-password MAL_PASSWORD
                        Provide password for MAL login (overrides password set in config)

Info:
  Info about the current anipy-cli installation

  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  --config-path         Print path to the config file.
```

# What it can do

- Faster than watching in the browser.
- Play Animes in Your Local video player
- Select a quality in which the video will be played/downloaded.
- Download Animes
- History of watched Episodes
- Binge Mode to watch a range of episodes back-to-back.
- Seasonal Mode to bulk download or binge watch the latest episodes of animes you pick
- Configurable with config
- (**Optional**) MAL Mode: Like seasonal mode, but uses your anime list at [MyAnimeList.net](https://myanimelist.net/)
- (**Optional**) Search GoGo for animes in specific seasons. Available for the download cli, seasonal mode and MAL mode. Turn it off with -o flag.
- (**Optional**) Discord Presence for the anime you currently watch. This is off by default, activate it in the config (-c)
- (**Optional**) Ffmpeg to download m3u8 playlists, may be more stable but is slower than internal downloader.

# Libary Usage

Documentation can be found [here](https://github.com/sdaqo/anipy-cli/blob/master/docs/anipycli_as_lib.py)

#### Important:

To import the libary, don't import `anipy-cli`, but `anipy_cli` (no '-' is allowed)

# Advanced Usage Examples
#### Little example of using anipy-cli for automatically keeping anime library up-to-date:
```
# Cronjob runs every 2 minutes and checks wether anipy-cli is still running or not 
# (only run the job if last one is finished)

*/2 *   * * *   username        pidof -x anipy-cli || anipy-cli -Ma >> /var/log/anipy-cli.log
```

# Other versions

- GUI Frontend by me (WIP): https://github.com/sdaqo/anipy-gui
- Dmenu script by @Dabbing-Guy: https://github.com/Dabbing-Guy/anipy-dmenu
- Ulauncher extension by @Dankni95 (not maintained):
  https://github.com/Dankni95/ulauncher-anime

# Credits

#### Heavily inspired by https://github.com/pystardust/ani-cli/

#### All contributors for contributing
