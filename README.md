


![waving](https://capsule-render.vercel.app/api?type=waving&height=200&text=sdaqo/anipy-cli&fontAlign=60&fontAlignY=40&color=021224&fontColor=b0b8b2&animation=fadeIn)


https://user-images.githubusercontent.com/63876564/162056019-ed0e7a60-78f6-4a2c-bc73-9be5dc2a4f07.mp4




### Little tool written in python to watch and download anime from the terminal (the better way to watch anime), also applicable as an API.
### Scrapes: https://gogoanime.gg

# Contents

- [Installation](#Installation)
- [Usage](#Usage)
- [Libary Usage](#libary-usage)
- [Other Versions](#other-versions)
- [Credits](#Credits)


# Installation

Recommended installation:

`python3 -m pip install anipy-cli`

Directly from the repo (may be newer):

`python3 -m pip install git+https://github.com/sdaqo/anipy-cli`

Other methodes can be found in [docs/install.md](https://github.com/sdaqo/anipy-cli/blob/master/docs/install.md)

For Videoplayback mpv is needed get it here: https://mpv.io/installation/

Optionally you can install [ffmpeg](https://ffmpeg.org/download.html) to download m3u8 playlists instead of the internal downloader. Use it with the -f flag. This is something you only want to enable when the internal downlaoder fails, since its pretty slow.

# Usage  
```
usage: anipy_cli.py [-h] [-q QUALITY] [-H] [-d] [-D] [-b] [-s] [-f] [-c]

Play Animes from gogoanime in local video-player or Download them.

options:
  -h, --help            show this help message and exit
  -q QUALITY, --quality QUALITY
                        Change the quality of the video, accepts: best, worst or 360, 480, 720 etc. Default: best
  -H, --history         Show your history of watched anime
  -d, --download        Download mode. Download multiple episodes like so: first_number-second_number (e.g. 1-3)
  -D, --delete-history  Delete your History.
  -b, --binge           Binge mode. Binge multiple episodes like so: first_number-second_number (e.g. 1-3)
  -s, --seasonal        Seasonal Anime mode. Bulk download or binge watch newest episodes.
  -f, --ffmpeg          Use ffmpeg to download m3u8 playlists, may be more stable but is way slower than internal downloader
  -c, --config          Print path to the config file.

```

# Libary Usage

Documentation can be found [here](https://github.com/sdaqo/anipy-cli/blob/master/docs/anipycli_as_lib.py)

#### Important:
To import the libary dont import `anipy-cli`, but `anipy_cli` (no '-' is allowed)

# Other versions
- Dmenu script by @Dabbing-Guy: https://github.com/Dabbing-Guy/anipy-dmenu 
- Ulauncher extension by @Dankni95 (not maintained): 
https://github.com/Dankni95/ulauncher-anime 


# Credits
#### Heavily inspired by https://github.com/pystardust/ani-cli/
#### All contributors for contributing
