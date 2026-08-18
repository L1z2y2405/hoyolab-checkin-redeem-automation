"""Tests for check-in response parsing."""

import httpx

from hoyo_auto.auth import GameAccount
from hoyo_auto.client import HoyoClient
from hoyo_auto.games.base import CheckInStatus, perform_check_in
from tests.conftest import json_response

ACCOUNT = GameAccount(
    uid="700001",
    nickname="Traveler",
    region="os_asia",
    level=60,
    cookie="ltoken_v2=x; ltuid_v2=y; ltmid_v2=z",
    redeem_enabled=True,
)


def test_check_in_already_signed(monkeypatch):
    calls = {"sign": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/info"):
            return json_response(
                {"retcode": 0, "data": {"total_sign_day": 5, "is_sign": True}}
            )
        if request.url.path.endswith("/home"):
            return json_response(
                {
                    "retcode": 0,
                    "data": {"awards": [{"name": "Primogem", "cnt": 90}]},
                }
            )
        if request.url.path.endswith("/sign"):
            calls["sign"] += 1
        return json_response({"retcode": 0})

    client = HoyoClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    result = perform_check_in(
        client,
        ACCOUNT,
        game="genshin",
        act_id="act",
        sign_game="hk4e",
        info_url="https://example.test/info",
        home_url="https://example.test/home",
        sign_url="https://example.test/sign",
    )

    assert result.status == CheckInStatus.ALREADY_SIGNED
    assert result.award_name == "Primogem"
    assert calls["sign"] == 0


def test_check_in_performs_sign_when_needed():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/info"):
            return json_response(
                {"retcode": 0, "data": {"total_sign_day": 2, "is_sign": False}}
            )
        if request.url.path.endswith("/home"):
            return json_response(
                {
                    "retcode": 0,
                    "data": {
                        "awards": [
                            {"name": "Mora", "cnt": 5000},
                            {"name": "Primogem", "cnt": 90},
                        ]
                    },
                }
            )
        if request.url.path.endswith("/sign"):
            return json_response({"retcode": 0, "message": "OK"})
        return json_response({"retcode": -1})

    client = HoyoClient()
    client._client = httpx.Client(transport=httpx.MockTransport(handler))

    result = perform_check_in(
        client,
        ACCOUNT,
        game="genshin",
        act_id="act",
        sign_game="hk4e",
        info_url="https://example.test/info",
        home_url="https://example.test/home",
        sign_url="https://example.test/sign",
    )

    assert result.status == CheckInStatus.SIGNED
    assert result.total_days == 3
    assert result.award_name == "Primogem"
