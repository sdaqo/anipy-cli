from anipy_cli import config
from pathlib import Path
import shutil

cfg_path = config.Config._get_config_path()
cfg_file = cfg_path / "config.yaml"
backup_path = Path(Path(__file__).parent)
backup_file = backup_path / "config.yaml"
config_test_file = backup_path / "config_for_tests.yaml"


def clear_and_backup():
    if cfg_file.exists():
        shutil.copy(cfg_file, backup_file)

        cfg_file.unlink()

    shutil.copy(config_test_file, cfg_file)


def revert():
    if backup_file.exists():
        shutil.copy(backup_file, cfg_file)
        backup_file.unlink()
