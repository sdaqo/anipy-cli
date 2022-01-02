from pathlib import Path

anipy_cli_folder = Path(Path(__file__).parent) # This will have to be changed if this file is moved
download_folder_path =  anipy_cli_folder / "download"
history_folder_path = anipy_cli_folder / "history"
history_file_path = history_folder_path / "history.txt"

gogoanime_url = "https://gogoanime.wiki/"

video_player_command = "mpv"
extra_player_commandline_options = ""