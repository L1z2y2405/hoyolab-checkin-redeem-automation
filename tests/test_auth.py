"""Tests for cookie parsing and account resolution."""

import httpx
import pytest

from hoyo_auto.auth import (
    extract_ltuid,
    filter_cookie,
    parse_cookie,
    resolve_game_account,
)
from hoyo_auto.client import HoyoClient
from tests.conftest import json_response

FULL_COOKIE = (
    "ltoken_v2=ltoken; ltuid_v2=12345; ltmid_v2=ltmid; "
    "cookie_token_v2=token; account_mid_v2=mid; account_id_v2=aid"
)


def test_parse_cookie_requires_checkin_fields():
    with pytest.raises(ValueError, match="ltoken_v2"):
        parse_cookie("ltuid_v2=1; ltmid_v2=2")


def test_parse_cookie_enables_redemption_with_token_fields():
    parsed = parse_cookie(FULL_COOKIE)
    assert parsed.redeem_enabled is True
    assert "ltoken_v2=ltoken" in parsed.checkin_cookie
    assert "cookie_token_v2=token" in parsed.checkin_cookie


def test_parse_cookie_disables_redemption_without_token_fields():
    parsed = parse_cookie("ltoken_v2=a; ltuid_v2=b; ltmid_v2=c")
    assert parsed.redeem_enabled is False


def test_extract_ltuid_supports_v2():
    assert extract_ltuid(FULL_COOKIE) == "12345"


def test_filter_cookie_whitelist():
    filtered = filter_cookie(
        FULL_COOKIE,
        ("cookie_token_v2", "account_id_v2"),
    )
    assert filtered == "cookie_token_v2=token; account_id_v2=aid"


def test_resolve_game_account_success(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            {
                "retcode": 0,
                "data": {
                    "list": [
                        {
                            "game_id": 2,
                            "game_role_id": "700001",
                            "nickname": "Traveler",
                            "region": "os_asia",
                            "level": 60,
                        }
                    ]
                },
            }
        )

    transport = httpx.MockTransport(handler)
    client = HoyoClient()
    client._client = httpx.Client(transport=transport)

    account = resolve_game_account(
        client,
        FULL_COOKIE,
        "12345",
        game_id=2,
        redeem_enabled=True,
        game_name="Genshin Impact",
    )
    assert account.uid == "700001"
    assert account.nickname == "Traveler"
    assert account.region == "os_asia"
