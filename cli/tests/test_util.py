"""Tests for anipy_cli.util helpers."""

from anipy_cli.util import parse_episode_ranges


def test_parse_episode_ranges_valid_input():
    assert parse_episode_ranges("1-2", [1, 2, 3]) == [1, 2]
    assert parse_episode_ranges("3", [1, 2, 3]) == [3]


def test_parse_episode_ranges_rejects_garbage(capsys):
    # Non-numeric range tokens must not crash with a ValueError traceback;
    # they are reported like any other invalid range and skipped.
    assert parse_episode_ranges("abc", [1, 2, 3]) == []
    assert "invalid range" in capsys.readouterr().err
