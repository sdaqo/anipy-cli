> ## Script working again, yeah, and quality selection as well. The workaround is done with Selenium and is pretty bad (inconvenient), I am going to try and make it better sometime.

# anipy-cli
### Little tool written in python to watch anime from the terminal (the better way to watch anime)
### Scrapes: https://gogoanime.wiki

TODO:
- [x] 📺 Search gogoanime and extract video url to play anime 
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

- `selenium`

- `geckodriver`

- `Firefox/Chrome or Chromium`

- `cURL`

- `mpv`
 

# Usage

## Install Dependencies

#### [Note] If you are on Linux you can skip step 1 (apart from firefox) and 3. Just do `sudo make all` to install dependencies and be able execute the script everywhere. To uninstall just do `sudo make uninstall`
 
### 1. Webdriver (Needs Firefox/Chrome/Chromium)
Webdriver is the render engine for browsers, it is needed for selenium. You need to have Firefox/Chrome/Chromium to use this script.

Installation:


#### Old installation, can skip to step 2
Windows:

- Download the latest build for your version of windows from: https://github.com/mozilla/geckodriver/releases
- Extract `geckodriver.exe` from the .zip file into any location
- Search for `Edit the system environment variables` and open the first entry. When the window pops up click on "Environment Variables"
- In the first box select the Variable named Path then click on Edit.
- Click the "New" button and type the Path to the folder where your `geckodriver.exe` is located. 
- Click on OK and close the windows. You are done.

Linux: 

On Arch-Based system the package `geckodriver` is already in the Community-Repo and can be installed like so: `sudo pacman -S geckodriver`. On Debian-Systems the installation is harder:

- Go to https://github.com/mozilla/geckodriver/releases and download the latest .tar.gz file for your system.
- Extract the file to any folder with `tar -xvzf geckodriver*`
- Make it executable with `chmod +x geckodriver`
- Add it to the PATH like so: `export PATH=$PATH:/path-to-extracted-file/`

### 2. Other dependencies
Get Python from: https://www.python.org/downloads/

Get mpv from: https://mpv.io/installation/

Curl should be preinstalled on Windows, Linux and macOS if not get it from here: https://curl.se/download.html

### 3. Python-Libs

To install `bs4`, `selenium` , `requests` and `webdriver-manager` open a terminal in the root-folder and execute `pip install -r requirements.txt`

## Start up 
To start `anipy-cli` do:

`python main.py`

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
#### Heavily inspired by https://github.com/pystardust/ani-cli/
#### Migueldeoleiros for the makefile 
