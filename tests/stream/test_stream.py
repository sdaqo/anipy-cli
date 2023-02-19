import pytest
from ..util import config_clearer
from anipy_cli import videourl, Entry


@pytest.fixture
def show_entry():
    config_clearer.clear_and_backup()

    show_entry = Entry(ep_url="https://gogoanime.tel/hyouka-episode-1")

    yield show_entry

    config_clearer.revert()


@pytest.mark.slow
def test_hyouka_extraction(show_entry):
    """Check if a stream url is being returned"""
    videourl_class = videourl(show_entry, "best")
    videourl_class.stream_url()

    show_entry = videourl_class.get_entry()

    assert show_entry.stream_url, "No stream url present"
