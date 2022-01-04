from pathlib import Path

# This will have to be changed if this file is moved
anipy_cli_folder = Path(Path(__file__).parent)

download_folder_path = anipy_cli_folder / "download"
history_folder_path = anipy_cli_folder / "history"
history_file_path = history_folder_path / "history.txt"

gogoanime_url = "https://gogoanime.wiki/"


mpv_path = "mpv"

# Leave at 'True' if you want integrated 
# playback resume, set to 'False' if you dont.  
mpv_resume_episode = True

# Specify mpv options like "--cache", 
# you will need to leave a space between
# each command. Look here for various
# commands: https://github.com/mpv-player/mpv/blob/master/DOCS/man/options.rst 
mpv_commandline_options = ""
