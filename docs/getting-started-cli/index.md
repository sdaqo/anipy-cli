# Getting started with the CLI

## Installation

### Pre-requesits
- [Python](https://www.python.org/downloads/) (3.9 higher, this is not tested ;) but I think that this is the case). If you are on windows avoid the python from the Microsoft Store and use the official one linked.
- [Pip](https://pip.pypa.io/en/stable/installation/)
- [Pipx](https://pipx.pypa.io/stable/installation/) (optional, but very much recommended, I mean it, get this)
- [mpv](https://mpv.io/) or any other player listed [here](../availabilty.md/#current-version), but I strongly recommended mpv or a derivative because it **✨ just works ✨**.
- [FFmpeg](https://ffmpeg.org/download.html) (optional, but again, I recommend it because without it you can not use some features)

### Options to install
- **Recommended: Via pipx**
    ```
    # Install
    pipx install anipy-cli
    
    # Update
    pipx upgrade anipy-cli
    
    # Uninstall
    pipx uninstall anipy-cli
    ```
- Via pipx (from source): 
```
# Install
pipx install "git+https://github.com/sdaqo/anipy-cli.git#subdirectory=cli"

# Update
pipx upgrade anipy-cli

# Uninstall
pipx uninstall anipy-cli
```
- Via pip: 
```
# Install
pip install anipy-cli

# Update
pip --upgrade anipy-cli

# Uninstall
pip uninstall anipy-cli
```
- Via pip (from source): 
```
# Install
pip install "git+https://github.com/sdaqo/anipy-cli.git#subdirectory=cli"

# Update
pip --upgrade anipy-cli

# Uninstall
pip uninstall anipy-cli
```
- NixOS: 
```
# Make sure you have flakes enabled on your system!

# Just run it once to try the program
nix run github:sdaqo/anipy-cli

# Add them to your flake inputs (recommended)
# 
# {
#   anipy-cli.url = "github:sdaqo/anipy-cli";
# }
#
# Use it with inputs.anipy-cli.${pkgs.system}.default
# For example:
#
# environment.systemPackages = [
#  inputs.anipy-cli.packages.${pkgs.system}.default
# ];

# Via Profile
nix profile install github:sdaqo/anipy-cli
nix profile update github:sdaqo/anipy-cli
nix profile list # Get the index of anipy-cli
nix profile remove <index-of-anipy-cli>
```

## Usage

=== "Explainations for non-obvious stuff"

    ### Seasonal Mode
    Seasonal Mode is one of the major modes of anipy-cli, with it you can
    manage your weekly dose of anime. Every new anime season you can add your
    anime you want to watch and check back every week to see if there are any new episodes!

    !!! info
        All major modes are listed under `Actions` in `anipy-cli --help`, you can only pick one of them.

    #### Check out the main menu of seasonal mode:
    ```
    [a] Add Anime
    [e] Delete one anime from seasonals
    [l] List anime in seasonals
    [c] Change dub/sub of anime in seasonals
    [d] Download newest episodes
    [w] Binge watch newest episodes
    [q] Quit
    Enter option:
    ```
    All these options should be pretty self-explanatory.

    ### MyAnimeList Mode
    MyAnimeList Mode is another major mode of anipy-cli. This mode is similar to the seasonal
    mode but it uses your anime list instead.

    #### Where do I put my login?
    There are several options:

    - Always login through the cli prompt.
    - Set username and password in the [config](#config)
    - Set the username in the config and pass the password via the `--mal-password` option.

    #### Anime Tagging in MyAnimeList
    You can tag (either via the cli using the `t` option or directly in MyAnimeList) your anime with a dub and a ignore tag.
    You can define the name of those tags in the config, the defaults are `dub` and `ignore`.

    **dub**
    : This tag makes the anime play/download in dub within the MAL mode.

    **ignore**
    : With this tag the anime will be completely ignored by the MAL mode.

    #### Check out the main menu of MAL mode.
    ```
    [a] Add Anime
    [e] Delete one anime from MyAnimeList
    [l] List anime in MyAnimeList
    [t] Tag anime in MyAnimeList (dub/ignore)
    [m] Map MyAnimeList anime to providers
    [s] Sync MyAnimeList into seasonals
    [b] Sync seasonals into MyAnimeList
    [d] Download newest episodes
    [x] Download all episodes
    [w] Binge watch newest episodes
    [q] Quit
    Enter option:
    ```

    The `m` option is **very important** it syncs the MyAnimeList anime to provider animeso we can actually get videos
    for the anime. You will be prompted for this anyway so do not worry to much, but it helps to run this every once in a while.

    The `s` option syncs all the anime in the status catagories specified in the config as `mal_status_catagories` to the
    seasonls, including episodes left of etc.

    The `b` option is the same as `s` but in the other direction.

    The `x` downloads **all** of the episodes instead of only the non-watched ones. This is pretty nice
    if you want to sync all the anime to your local disk, just run it once in a while (maybe even with [Auto Update](#auto-update)) to
    keep everything in-sync, it will skip already downloaded ones.

    ### Auto Update
    Auto update is a flag in anipy-cli: `--auto-update` it will automatically update and download all anime in seasonals or mal mode from start
    episode to newest. This is increadibly handy if you want to set up some [cron job](https://de.wikipedia.org/wiki/Cron) to keep your library up-to-date.

    !!! note
        This only works in combination with `-M` or `-S`

    Here is a example for a cron job:
    ```
    # Cronjob runs every 2 minutes and checks whether anipy-cli is still running or not
    # (only run the job if last one is finished)

    */2 *   * * *   username        pidof -x anipy-cli || anipy-cli -Ma >> /var/log/anipy-cli.log
    ```

    ### Other weird options
    `--mal-sync-to-seasonals`
    : This options just automatically executes the `s` option in the MAL mode menu. Useful for automation.

    `--ffmpeg`
    : This makes the downloader default the [ffmpeg](https://ffmpeg.org/) (except for .mp4 files), ffmpeg must be [installed](https://ffmpeg.org/download.html).

=== "Help Output"

    This is just a paste from `anipy-cli --help`.
    ```
    usage: anipy-cli [-D | -B | -H | -S | -M | --delete-history] [-s SEARCH] [-q QUALITY] [-f] [-o] [-a] [-p {mpv,vlc,syncplay,mpvnet}] [-l LOCATION] [--mal-password MAL_PASSWORD] [--mal-sync-to-seasonals] [-h] [-v] [--config-path]

    Play Animes from online anime providers locally or download them, and much more.

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

      -s SEARCH, --search SEARCH
                            Provide a search term to the Download or Binge mode in this format: {query}:{episode range}:{dub/sub}. Examples: 'frieren:1-10:sub' or 'frieren:1:sub' or 'frieren:1-3 7-12:dub'
      -q QUALITY, --quality QUALITY
                            Change the quality of the video, accepts: best, worst or 360, 480, 720 etc. Default: best
      -f, --ffmpeg          Use ffmpeg to download m3u8 playlists, may be more stable but is way slower than internal downloader
      -a, --auto-update     Automatically update and download all Anime in seasonals or mal mode from start EP to newest.
      -p {mpv,vlc,syncplay,mpvnet,mpv-controlled}, --optional-player {mpv,vlc,syncplay,mpvnet, mpv-controlled}
                            Override the player set in the config.
      -l LOCATION, --location LOCATION
                            Override all configured download locations
      --mal-password MAL_PASSWORD
                            Provide password for MAL login (overrides password set in config)
      --mal-sync-to-seasonals
                            Automatically sync myanimelist to seasonals (only works with `-M`)

    Info:
      Info about the current anipy-cli installation

      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      --config-path         Print path to the config file.

    ```

## Config

### Config Locations (normally, better use `--config-path`):

- Linux/Unix: ~/.config/anipy-cli/config.yaml
- MacOS: /Library/Application Support/anipy-cli/config.yaml
- Windows: C:\Users\%USERPROFILE%\AppData\Local\anipy-cli

**For convinience's sake there is a extra cli option that gives you the config
path:**

```shell
anipy-cli --config-path
/path/to/your/config.yaml
```

### Configuring

All the options should be documented with comments, please use those as
reference, if you are confused just
[open an issue](https://github.com/sdaqo/anipy-cli/issues)!

## Features

- Faster than watching in the browser.
- Play Animes in Your Local video player
- Select a quality in which the video will be played/downloaded.
- Download Animes
- History of watched Episodes
- Binge Mode to watch a range of episodes back-to-back.
- Seasonal Mode to bulk download or binge watch the latest episodes of animes
  you pick
- Configurable with config
- MAL Mode: Like seasonal mode, but uses your anime list at
  [MyAnimeList.net](https://myanimelist.net/)
- Discord Presence for the anime you currently watch. This is off by default,
  activate it in the config.
