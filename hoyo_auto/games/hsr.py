"""Honkai: Star Rail check-in and code redemption."""

from __future__ import annotations

import logging
import time

from hoyo_auto.auth import REDEEM_COOKIE_KEYS, GameAccount, filter_cookie, resolve_game_account
from hoyo_auto.client import HoyoClient
from hoyo_auto.errors import FailureKind, classify_retcode
from hoyo_auto.games.base import CheckInResult, RedeemResult, perform_check_in

logger = logging.getLogger(__name__)

GAME_ID = 6
GAME_NAME = "Honkai: Star Rail"
GAME_KEY = "hsr"
ACT_ID = "e202303301540311"
SIGN_GAME = "hkrpg"

INFO_URL = "https://sg-public-api.hoyolab.com/event/luna/os/info"
HOME_URL = "https://sg-public-api.hoyolab.com/event/luna/os/home"
SIGN_URL = "https://sg-public-api.hoyolab.com/event/luna/os/sign"
REDEEM_URL = "https://sg-hkrpg-api.hoyoverse.com/common/apicdkey/api/webExchangeCdkeyRisk"
CODE_SOURCE_URL = "https://api.ennead.cc/mihoyo/starrail/codes"


def login(client: HoyoClient, cookie: str, ltuid: str, redeem_enabled: bool) -> GameAccount:
    account = resolve_game_account(
        client, cookie, ltuid, GAME_ID, redeem_enabled, GAME_NAME
    )
    logger.info(
        "%s: logged in as %s (UID %s, region %s)",
        GAME_NAME,
        account.nickname,
        account.uid,
        account.region,
    )
    return account


def check_in(client: HoyoClient, account: GameAccount) -> CheckInResult:
    return perform_check_in(
        client,
        account,
        game=GAME_KEY,
        act_id=ACT_ID,
        sign_game=SIGN_GAME,
        info_url=INFO_URL,
        home_url=HOME_URL,
        sign_url=SIGN_URL,
    )


def fetch_codes(client: HoyoClient) -> list[dict]:
    response = client.get(CODE_SOURCE_URL, hoyolab=False)
    if response.status_code != 200:
        logger.debug("%s: code source returned HTTP %s", GAME_NAME, response.status_code)
        return []

    body = response.json()
    active = body.get("active")
    if not isinstance(active, list):
        logger.debug("%s: code source returned malformed payload", GAME_NAME)
        return []

    return [
        {"code": str(item.get("code", "")).strip(), "rewards": item.get("rewards") or []}
        for item in active
        if item.get("code")
    ]


def redeem_code(client: HoyoClient, account: GameAccount, code: str) -> RedeemResult:
    if not account.redeem_enabled:
        return RedeemResult(
            success=False,
            code=code,
            game=GAME_KEY,
            message="Redemption disabled — cookie missing token fields",
            cache_code=False,
        )

    redeem_cookie = filter_cookie(account.cookie, REDEEM_COOKIE_KEYS)
    response = client.post(
        REDEEM_URL,
        params={
            "uid": account.uid,
            "region": account.region,
            "lang": "en",
            "cdkey": code,
            "game_biz": "hkrpg_global",
            "t": int(time.time() * 1000),
        },
        headers={"Cookie": redeem_cookie},
    )

    if response.status_code != 200:
        return RedeemResult(
            success=False,
            code=code,
            game=GAME_KEY,
            message=f"HTTP {response.status_code}",
            cache_code=False,
        )

    body = response.json()
    retcode = body.get("retcode", -1)
    kind, message, cache = classify_retcode(retcode)
    success = kind == FailureKind.SUCCESS

    if success:
        logger.info("%s: redeemed code %s", GAME_NAME, code)
    elif kind in (FailureKind.EXPIRED, FailureKind.INVALID, FailureKind.ALREADY_DONE):
        logger.info("%s: code %s — %s", GAME_NAME, code, message)
    else:
        logger.warning("%s: code %s — %s", GAME_NAME, code, message)

    return RedeemResult(
        success=success,
        code=code,
        game=GAME_KEY,
        message=message if retcode != 0 else body.get("message", "Redeemed"),
        cache_code=cache,
    )


def redeem_with_delay(
    client: HoyoClient,
    account: GameAccount,
    codes: list[str],
    delay_seconds: float,
) -> list[RedeemResult]:
    results: list[RedeemResult] = []
    for index, code in enumerate(codes):
        if index > 0:
            time.sleep(delay_seconds)
        results.append(redeem_code(client, account, code))
    return results
