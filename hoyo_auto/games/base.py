"""Shared check-in types and helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum

from hoyo_auto.auth import GameAccount
from hoyo_auto.client import HoyoClient
from hoyo_auto.errors import classify_retcode


class CheckInStatus(str, Enum):
    SIGNED = "signed"
    ALREADY_SIGNED = "already_signed"
    FAILED = "failed"


@dataclass(frozen=True)
class CheckInResult:
    status: CheckInStatus
    game: str
    nickname: str
    uid: str
    total_days: int | None = None
    award_name: str | None = None
    award_count: int | None = None
    message: str = ""


@dataclass(frozen=True)
class RedeemResult:
    success: bool
    code: str
    game: str
    message: str
    cache_code: bool


def _parse_sign_info(body: dict) -> tuple[int, bool]:
    data = body.get("data") or {}
    return int(data.get("total_sign_day", 0)), bool(data.get("is_sign"))


def _today_award(awards: list[dict], total_signed: int) -> tuple[str, int]:
    if not awards:
        return "Unknown", 0
    index = min(total_signed, len(awards) - 1)
    award = awards[index]
    return str(award.get("name", "Unknown")), int(award.get("cnt", 0))


def perform_check_in(
    client: HoyoClient,
    account: GameAccount,
    *,
    game: str,
    act_id: str,
    sign_game: str,
    info_url: str,
    home_url: str,
    sign_url: str,
) -> CheckInResult:
    failed = CheckInResult(
        status=CheckInStatus.FAILED,
        game=game,
        nickname=account.nickname,
        uid=account.uid,
    )
    headers = {"Cookie": account.cookie, "x-rpc-signgame": sign_game}
    params = {"act_id": act_id}

    info_resp = client.get(info_url, params=params, headers=headers)
    if info_resp.status_code != 200:
        return replace(failed, message=f"Sign info HTTP {info_resp.status_code}")

    info_body = info_resp.json()
    if info_body.get("retcode") != 0:
        kind, message, _ = classify_retcode(info_body.get("retcode", -1))
        return replace(failed, message=f"{message} ({kind.value})")

    total, is_signed = _parse_sign_info(info_body)

    home_resp = client.get(home_url, params=params, headers=headers)
    if home_resp.status_code != 200:
        return replace(failed, message=f"Awards HTTP {home_resp.status_code}")

    home_body = home_resp.json()
    if home_body.get("retcode") != 0:
        kind, message, _ = classify_retcode(home_body.get("retcode", -1))
        return replace(failed, message=f"{message} ({kind.value})")

    awards = (home_body.get("data") or {}).get("awards") or []
    award_name, award_count = _today_award(awards, total)

    if is_signed:
        return CheckInResult(
            status=CheckInStatus.ALREADY_SIGNED,
            game=game,
            nickname=account.nickname,
            uid=account.uid,
            total_days=total,
            award_name=award_name,
            award_count=award_count,
            message="Already checked in today",
        )

    sign_resp = client.post(sign_url, params=params, headers=headers)
    if sign_resp.status_code != 200:
        return replace(failed, message=f"Sign HTTP {sign_resp.status_code}")

    sign_body = sign_resp.json()
    if sign_body.get("retcode") != 0:
        kind, message, _ = classify_retcode(sign_body.get("retcode", -1))
        return replace(failed, message=f"{message} ({kind.value})")

    return CheckInResult(
        status=CheckInStatus.SIGNED,
        game=game,
        nickname=account.nickname,
        uid=account.uid,
        total_days=total + 1,
        award_name=award_name,
        award_count=award_count,
        message="Check-in successful",
    )
