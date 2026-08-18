"""Tests for code discovery normalization and redemption handling."""

import httpx

from hoyo_auto.auth import GameAccount
from hoyo_auto.client import HoyoClient
from hoyo_auto.games import genshin, hsr
from hoyo_auto.redeem import _normalize_codes
from tests.conftest import json_response

ACCOUNT = GameAccount(
    uid="800001",
    nickname="Trailblazer",
    region="prod_gf_jp",
    level=70,
    cookie=(
        "ltoken_v2=a; ltuid_v2=b; ltmid_v2=c; "
        "cookie_token_v2=t; account_mid_v2=m; account_id_v2=i"
    ),
    redeem_enabled=True,
)


def test_normalize_codes_deduplicates_and_uppercases():
    codes = _normalize_codes(
        [
            {"code": "abc123"},
            {"code": "ABC123"},
            {"code": "xyz789"},
            {"code": ""},
        ]
    )
    assert codes == ["ABC123", "XYZ789"]


def test_genshin_fetch_codes_parses_active_list():
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response(
            {
                "active": [
                    {"code": "GENSHIN2026", "rewards": ["Primogem x60"]},
                ]
            }
        )

    client = HoyoClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    codes = genshin.fetch_codes(client)
    assert codes[0]["code"] == "GENSHIN2026"


def test_hsr_redeem_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        return json_response({"retcode": 0, "message": "OK"})

    client = HoyoClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    result = hsr.redeem_code(client, ACCOUNT, "HSR2026")
    assert result.success is True
    assert result.cache_code is True


def test_genshin_redeem_expired_code_is_cached():
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response({"retcode": -2001, "message": "expired"})

    client = HoyoClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    result = genshin.redeem_code(client, ACCOUNT, "OLD123")
    assert result.success is False
    assert result.cache_code is True


def test_genshin_redeem_busy_is_not_cached():
    def handler(request: httpx.Request) -> httpx.Response:
        return json_response({"retcode": -1048, "message": "busy"})

    client = HoyoClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))
    result = genshin.redeem_code(client, ACCOUNT, "NEW123")
    assert result.cache_code is False
