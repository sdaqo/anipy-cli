#################################################################################################
#                                                                                               #
#           ANIPY-CLI DEFAULT CONFIGURATION                                                     #
#                                                                                               #
#           This file gets overwritten with every update!                                       #
#                                                                                               #
#           Copy config.py to config_personal.py and make your changes there!!                  #
#                                                                                               #
#################################################################################################


try:
    from .config_personal import config

except ImportError:

    from pathlib import Path

    class config:
        # This will have to be changed if this file is moved
        anipy_cli_folder = Path(Path(__file__).parent)

        # These are the paths used by anipy-cli to store data
        # They are all pathlib.Path objects

        # In order to specify a relative path, use the / operator
        # Ex. ~/Downloads/anipy would be Path.home() / 'Downloads' / 'anipy'
        # You could also just use a regular path string and turn it into a Path object
        # Ex. ~/Downloads/anipy would be Path('~/Downloads/anipy')

        download_folder_path = anipy_cli_folder / "download"
        seasonals_dl_path = download_folder_path / "seasonals"
        user_files_path = anipy_cli_folder / "user_files"
        history_file_path = user_files_path / "history.json"
        seasonal_file_path = user_files_path / "seasonals.json"

        gogoanime_url = "https://gogoanime.gg/"

        # Path to the video-player.
        # Supported Players are: mpv, vlc, syncplay, mpvnet
        player_path = "mpv"

        # Specify additional mpv/vlc options (syncplay uses the same options as mpv)
        # You will need to leave a comma (,) between
        # each command and every command should
        # be wrappedd in quotes (").
        # Example (for mpv): ["--fs", "--cache"]
        # Look here for various commands:
        #   - mpv: https://github.com/mpv-player/mpv/blob/master/DOCS/man/options.rst
        #   - vlc: https://wiki.videolan.org/VLC_command-line_help/
        mpv_commandline_options = []
        vlc_commandline_options = []
        
        # Reuse the mpv window instead of closing and reopening.
        # This uses python-mpv, wich uses libmpv, on linux this is preinstalled
        # with mpv on windows you have to get the mpv-2.dll file from here:
        # https://sourceforge.net/projects/mpv-player-windows/files/libmpv/
        reuse_mpv_window = False

        # Always use ffmpeg to download hls streams, you can
        # also activate this temprarly using the -f flag when
        # downloading something.
        # Default: False
        ffmpeg_hls = False
        # The log of the ffmpeg process, when its used
        ffmpeg_log_path = user_files_path / "ffmpeg_log"

        # This determines how downloaded anime will be named
        # The following variables can be used: show_name, episode_number, quality
        download_name_format = "{show_name}_{episode_number}.mp4"

        # This removes the (Dub) in the anime title when downloading
        download_remove_dub_from_folder_name = False

        # Discord Presence:
        # Show what you are watching on discord
        # Default: False
        dc_presence = False
