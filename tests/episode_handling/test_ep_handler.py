from anipy_cli import epHandler, entry
from urllib.parse import urlparse


def test_gen_link_regular():
    """Test link generation on a regular show with a regular episode"""
    show_entry = epHandler(
        entry(category_url="https://gogoanime.tel/category/hyouka", ep=1)
    ).gen_eplink()

    assert (
        urlparse(show_entry.ep_url).path == "//hyouka-episode-1"
    ), "Wrong link generated"


def test_gen_link_with_unknown_chars():
    """Test link generation with a show with unkown charachters
    in its title (e.g. Saenai Heroine no Sodatekata ♭)"""

    show_entry = epHandler(
        entry(
            category_url="https://gogoanime.tel/category/saenai-heroine-no-sodatekata-2",
            ep=1,
        )
    ).gen_eplink()

    assert (
        urlparse(show_entry.ep_url).path == "//saenai-heroine-no-sodatekata-2-1"
    ), "Wrong link generated"


def test_gen_link_special():
    """Test link generation with a special episode (e.g. 7.5)"""

    show_entry = epHandler(
        entry(category_url="https://gogoanime.tel/category/86-2nd-season", ep=7.5)
    ).gen_eplink()

    assert (
        urlparse(show_entry.ep_url).path == "//86-2nd-season-episode-7-5"
    ), "Wrong link generated"


def test_gen_latest():
    """Test last ep gen"""
    last_ep = epHandler(
        entry(category_url="https://gogoanime.tel/category/hyouka")
    ).get_latest()

    assert last_ep == 22, "Not last Episode"


def test_gen_first_ep():
    """Test first ep gen"""
    first_ep = epHandler(
        entry(category_url="https://gogoanime.tel/category/hyouka")
    ).get_first()

    assert int(first_ep) == 1, "Not first Episode"


def test_next_ep():
    show_entry = epHandler(
        entry(category_url="https://gogoanime.tel/category/hyouka", ep=1)
    ).next_ep()

    assert show_entry.ep == 2, "Wrong episode"
    assert "2" in show_entry.ep_url, "Wrong episode url"


def test_prev_ep():
    show_entry = epHandler(
        entry(category_url="https://gogoanime.tel/category/hyouka", ep=3)
    ).prev_ep()

    assert show_entry.ep == 2, "Wrong episode"
    assert "2" in show_entry.ep_url, "Wrong episode url"
