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
    for name in (
        "HOYOLAB_COOKIE",
        "ENABLE_GENSHIN",
        "ENABLE_HSR",
        "ENABLE_HSR_CHECKIN",
        "ENABLE_HSR_REDEEM",
        "STATE_DIR",
    ):
        monkeypatch.delenv(name, raising=False)
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
    assert settings.enable_hsr_checkin is True
    assert settings.enable_hsr_redeem is True
    assert settings.state_dir == Path("custom-data")


def test_hsr_checkin_can_be_disabled_while_redeem_stays_on(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("HOYOLAB_COOKIE", raising=False)
    monkeypatch.delenv("ENABLE_HSR_CHECKIN", raising=False)
    monkeypatch.delenv("ENABLE_HSR_REDEEM", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "HOYOLAB_COOKIE=ltoken_v2=a; ltuid_v2=1; ltmid_v2=b",
                "ENABLE_HSR=true",
                "ENABLE_HSR_CHECKIN=false",
                "ENABLE_HSR_REDEEM=true",
            ]
        ),
        encoding="utf-8",
    )
    settings = Settings.load(str(env_file))
    assert settings.enable_hsr_checkin is False
    assert settings.enable_hsr_redeem is True
