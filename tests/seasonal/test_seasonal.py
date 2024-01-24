import pytest
from hashlib import md5
from ..util import config_clearer
from anipy_cli import Seasonal, config


@pytest.fixture
def show_details():
    config_clearer.clear_and_backup()

    config.Config().seasonal_file_path.unlink(missing_ok=True)

    yield ("Hyouka", "https://gogoanime.tel/category/hyouka", 1)

    config_clearer.revert()


def test_add_hyouka(show_details):
    """Check if adding works"""
    MD5 = "536968369fffedaf4c5461d01021b624"

    Seasonal().add_show(*show_details)

    assert _check_md5(MD5), "MD5 mismatch"


def test_del_hyouka(show_details):
    """Check if deleting an entry works"""
    MD5 = "99914b932bd37a50b983c5e7c90ae93b"

    Seasonal().add_show(*show_details)
    Seasonal().del_show(show_details[0])

    assert _check_md5(MD5), "MD5 mismatch"


def test_update_hyouka(show_details):
    """Check if updating a show works"""
    MD5 = "0dc5e6db1089f5e9ccf42f1ed443076c"

    Seasonal().add_show(*show_details)
    Seasonal().update_show(show_details[0], show_details[1])

    assert _check_md5(MD5), "MD5 mismatch"


@pytest.mark.slow
def test_latest_eps_hyouka(show_details):
    """Check if the right latest eps are being returned"""

    CORRECT_OUTPUT = {
        "Hyouka": {
            "ep_list": [
                [2, "https://gogoanime.gg//hyouka-episode-2"],
                [3, "https://gogoanime.gg//hyouka-episode-3"],
                [4, "https://gogoanime.gg//hyouka-episode-4"],
                [5, "https://gogoanime.gg//hyouka-episode-5"],
                [6, "https://gogoanime.gg//hyouka-episode-6"],
                [7, "https://gogoanime.gg//hyouka-episode-7"],
                [8, "https://gogoanime.gg//hyouka-episode-8"],
                [9, "https://gogoanime.gg//hyouka-episode-9"],
                [10, "https://gogoanime.gg//hyouka-episode-10"],
                [11, "https://gogoanime.gg//hyouka-episode-11"],
                [12, "https://gogoanime.gg//hyouka-episode-12"],
                [13, "https://gogoanime.gg//hyouka-episode-13"],
                [14, "https://gogoanime.gg//hyouka-episode-14"],
                [15, "https://gogoanime.gg//hyouka-episode-15"],
                [16, "https://gogoanime.gg//hyouka-episode-16"],
                [17, "https://gogoanime.gg//hyouka-episode-17"],
                [18, "https://gogoanime.gg//hyouka-episode-18"],
                [19, "https://gogoanime.gg//hyouka-episode-19"],
                [20, "https://gogoanime.gg//hyouka-episode-20"],
                [21, "https://gogoanime.gg//hyouka-episode-21"],
                [22, "https://gogoanime.gg//hyouka-episode-22"],
            ],
            "category_url": "https://gogoanime.tel/category/hyouka",
        }
    }

    Seasonal().add_show(*show_details)
    latest = Seasonal().latest_eps()

    assert latest == CORRECT_OUTPUT, "Output differs"


def _check_md5(md5_sum):
    with config.Config().seasonal_file_path.open("rb") as fb:
        md5sum_from_file = md5(fb.read()).hexdigest()

    return md5_sum == md5sum_from_file
