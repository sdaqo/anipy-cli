import pytest
import sys
import shutil
from anipy_cli import entry, download, videourl, config
from ..util import config_clearer


@pytest.fixture
def show_entry():
    show_entry = entry(
        show_name="Hyouka",
        category_url="https://gogoanime.tel/category/hyouka",
        ep_url="https://gogoanime.tv/hyouka-episode-1",
        ep=1,
        latest_ep=22,
    )

    videourl_class = videourl(entry=show_entry, quality="worst")
    videourl_class.stream_url()

    show_entry = videourl_class.get_entry()

    config_clearer.clear_and_backup()

    yield show_entry

    config_clearer.revert()


@pytest.mark.veryslow
def test_hyouka_noffmpeg(show_entry):
    shutil.rmtree(
        config.Config().download_folder_path / show_entry.show_name, ignore_errors=True
    )

    download_class = download(entry=show_entry, quality="max", ffmpeg=False)
    download_class.download()

    download_path = download_class.show_folder / download_class._get_fname()

    assert download_path.is_file(), f"File was not created {download_path}"
    assert (
        download_path.stat().st_size > 10000000
    ), f"File is smaller than 10MB, maybe it wasnt correctly downloaded?"

    download_path.unlink()


@pytest.mark.veryslow
def test_hyouka_ffmpeg(show_entry):
    shutil.rmtree(
        config.Config().download_folder_path / show_entry.show_name, ignore_errors=True
    )

    download_class = download(entry=show_entry, quality="max", ffmpeg=True)
    download_class.download()

    download_path = download_class.show_folder / download_class._get_fname()

    assert download_path.is_file(), f"File was not created {download_path}"
    assert (
        download_path.stat().st_size > 10000000
    ), f"File is smaller than 10MB, maybe it wasnt correctly downloaded?"

    download_path.unlink()
