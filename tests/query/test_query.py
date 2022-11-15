import pytest
from anipy_cli import entry, query


@pytest.mark.slow
def test_naruto():
    query_class = query("Naruto", entry())
    res = query_class.get_links()

    assert res != 0

    links, names = res

    assert links[0] == "/category/naruto" and names[0] == "Naruto"
