"""Tests for configuration loading."""

from pathlib import Path

import pytest

from hoyo_auto.config import Settings


def test_settings_requires_cookie(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("HOYOLAB_COOKIE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("HOYOLAB_COOKIE=\n", encoding="utf-8")
    with pytest.raises(ValueError, match="HOYOLAB_COOKIE"):
        Settings.load(str(env_file))


def test_settings_loads_from_env_file(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("HOYOLAB_COOKIE", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "HOYOLAB_COOKIE=ltoken_v2=a; ltuid_v2=1; ltmid_v2=b",
                "ENABLE_GENSHIN=false",
                "ENABLE_HSR=true",
                "STATE_DIR=custom-data",
            ]
        ),
        encoding="utf-8",
    )
    settings = Settings.load(str(env_file))
    assert settings.enable_genshin is False
    assert settings.enable_hsr is True
    assert settings.state_dir == Path("custom-data")
