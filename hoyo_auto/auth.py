"""Cookie parsing and account resolution."""

from __future__ import annotations

import re
from dataclasses import dataclass

from hoyo_auto.client import HoyoClient
from hoyo_auto.errors import classify_retcode


CHECKIN_COOKIE_KEYS = ("ltoken_v2", "ltuid_v2", "ltmid_v2")
REDEEM_COOKIE_KEYS = (
    "cookie_token_v2",
    "account_mid_v2",
    "account_id_v2",
    "cookie_token",
    "account_id",
)

GAME_RECORD_URL = (
    "https://bbs-api-os.hoyolab.com/game_record/card/wapi/getGameRecordCard"
)


@dataclass(frozen=True)
class ParsedCookie:
    checkin_cookie: str
    redeem_enabled: bool


@dataclass(frozen=True)
class GameAccount:
    uid: str
    nickname: str
    region: str
    level: int
    cookie: str
    redeem_enabled: bool


def _cookie_map(raw: str) -> dict[str, str]:
    pairs: dict[str, str] = {}
    for part in raw.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        key, value = part.split("=", 1)
        pairs[key.strip()] = value.strip()
    return pairs


def parse_cookie(raw: str) -> ParsedCookie:
    cookies = _cookie_map(raw)
    missing = [k for k in CHECKIN_COOKIE_KEYS if not cookies.get(k)]
    if missing:
        raise ValueError(
            f"Cookie missing required fields for check-in: {', '.join(missing)}"
        )

    redeem_keys = ("cookie_token_v2", "account_mid_v2", "account_id_v2")
    redeem_enabled = all(cookies.get(k) for k in redeem_keys)

    checkin_cookie = "; ".join(f"{k}={cookies[k]}" for k in CHECKIN_COOKIE_KEYS)
    if redeem_enabled:
        checkin_cookie += "; " + "; ".join(f"{k}={cookies[k]}" for k in redeem_keys)

    return ParsedCookie(checkin_cookie=checkin_cookie, redeem_enabled=redeem_enabled)


def filter_cookie(raw: str, whitelist: tuple[str, ...]) -> str:
    cookies = _cookie_map(raw)
    parts = [f"{k}={cookies[k]}" for k in whitelist if cookies.get(k)]
    return "; ".join(parts)


def extract_ltuid(raw: str) -> str:
    match = re.search(r"ltuid(?:_v2)?=([^;]+)", raw)
    if not match:
        raise ValueError("Could not find ltuid or ltuid_v2 in HOYOLAB_COOKIE")
    return match.group(1)


def resolve_game_account(
    client: HoyoClient,
    cookie: str,
    ltuid: str,
    game_id: int,
    redeem_enabled: bool,
    game_name: str,
) -> GameAccount:
    response = client.get(
        GAME_RECORD_URL,
        params={"uid": ltuid},
        headers={"Cookie": cookie},
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"{game_name}: game record lookup failed (HTTP {response.status_code})"
        )

    body = response.json()
    retcode = body.get("retcode")
    if retcode != 0:
        kind, message, _ = classify_retcode(retcode)
        raise RuntimeError(f"{game_name}: login failed — {message} (retcode={retcode}, kind={kind.value})")

    data = body.get("data") or {}
    accounts = data.get("list") or []
    match = next((a for a in accounts if a.get("game_id") == game_id), None)
    if not match:
        raise RuntimeError(
            f"{game_name}: no linked game account found for game_id={game_id}"
        )

    return GameAccount(
        uid=str(match["game_role_id"]),
        nickname=str(match.get("nickname", "Unknown")),
        region=str(match["region"]),
        level=int(match.get("level", 0)),
        cookie=cookie,
        redeem_enabled=redeem_enabled,
    )
