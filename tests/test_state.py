"""Tests for local code state/cache."""

from pathlib import Path

from hoyo_auto.state import CodeState


def test_bootstrap_seeds_without_redeeming(tmp_path: Path):
    state = CodeState(tmp_path / "state.json")
    bootstrapped = state.bootstrap_if_empty("genshin", ["abc123", "def456"])
    assert bootstrapped is True
    assert state.get_codes("genshin") == {"ABC123", "DEF456"}


def test_filter_new_ignores_cached_and_duplicates(tmp_path: Path):
    state = CodeState(tmp_path / "state.json")
    state.add_codes("genshin", {"OLD123"})
    new_codes = state.filter_new("genshin", ["old123", "new999", "new999"])
    assert new_codes == ["NEW999"]


def test_add_codes_persists(tmp_path: Path):
    path = tmp_path / "state.json"
    state = CodeState(path)
    state.add_codes("hsr", {"STAR1"})
    reloaded = CodeState(path)
    assert reloaded.get_codes("hsr") == {"STAR1"}
