import pytest
from anipy_cli import config
from pathlib import Path, PosixPath
import shutil


@pytest.fixture()
def resource():
    """Setup Phase"""

    cfg_path = config.Config._get_config_path()
    cfg_file = cfg_path / "config.yaml"
    config_test_path = Path(Path(__file__).parent)

    user_conf_backup = config_test_path / "config.yaml"

    if cfg_file.exists():
        shutil.copy(cfg_file, user_conf_backup)

    shutil.copy(config_test_path / "test_config.yaml", cfg_file)

    yield config.Config()

    """Teardown Phase"""

    shutil.copy(user_conf_backup, cfg_file)

    user_conf_backup.unlink()


def test_config_values(resource: config.Config):
    correct_values = {
        "download_folder_path": PosixPath("~/anipy-cli/downloads/common").expanduser(),
        "seasonals_dl_path": PosixPath("~/anipy-cli/downloads/seasonals").expanduser(),
        "user_files_path": PosixPath("~/anipy-cli/user_files").expanduser(),
        "gogoanime_url": "https://gogoanime.gg/",
        "ffmpeg_log_path": PosixPath("~/anipy-cli/user_files/ffmpeg_log").expanduser(),
        "history_file_path": PosixPath("~/anipy-cli/user_files/history.json").expanduser(),
        "seasonal_file_path": PosixPath("~/anipy-cli/user_files/seasonals.json").expanduser(),
        "player_path": "mpv",
        "mpv_commandline_options": ["--fs", "--cache"],
        "vlc_commandline_options": [],
        "reuse_mpv_window": False,
        "ffmpeg_hls": False,
        "download_name_format": "{show_name} - {episode_number} - {quality}.mp4",
        "download_remove_dub_from_folder_name": True,
        "dc_presence": False,
    }

    for prop in dir(resource):
        if prop.startswith("_"):
            continue

        assert correct_values[str(prop)] == getattr(
            resource, prop
        ), f"Config value {prop} is not correct"
