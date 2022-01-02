from pathlib import Path

# This will have to be changed if this file is moved
anipy_cli_folder = Path(Path(__file__).parent)

download_folder_path = anipy_cli_folder / "download"
history_folder_path = anipy_cli_folder / "history"
history_file_path = history_folder_path / "history.txt"

gogoanime_url = "https://gogoanime.wiki/"

mpv_path = "mpv"
mpv_commandline_options = ""