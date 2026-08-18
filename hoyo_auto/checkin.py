"""Orchestrate daily check-in for enabled games."""

from __future__ import annotations

import logging

from hoyo_auto.auth import GameAccount, extract_ltuid, parse_cookie
from hoyo_auto.client import HoyoClient
from hoyo_auto.config import Settings
from hoyo_auto.games import genshin, hsr
from hoyo_auto.games.base import CheckInResult, CheckInStatus

logger = logging.getLogger(__name__)


def _log_check_in(result: CheckInResult) -> None:
    label = result.game.upper()
    if result.status == CheckInStatus.SIGNED:
        logger.info(
            "[%s] %s (%s): check-in successful — day %s, reward %s x%s",
            label,
            result.nickname,
            result.uid,
            result.total_days,
            result.award_name,
            result.award_count,
        )
    elif result.status == CheckInStatus.ALREADY_SIGNED:
        logger.info(
            "[%s] %s (%s): already checked in today (day %s)",
            label,
            result.nickname,
            result.uid,
            result.total_days,
        )
    else:
        logger.error(
            "[%s] %s (%s): check-in failed — %s",
            label,
            result.nickname,
            result.uid,
            result.message,
        )


def run_check_in(settings: Settings, client: HoyoClient) -> list[CheckInResult]:
    parsed = parse_cookie(settings.cookie)
    ltuid = extract_ltuid(settings.cookie)
    results: list[CheckInResult] = []

    if settings.enable_genshin:
        try:
            account = genshin.login(client, parsed.checkin_cookie, ltuid, parsed.redeem_enabled)
            result = genshin.check_in(client, account)
            results.append(result)
            _log_check_in(result)
        except Exception as exc:
            logger.error("Genshin check-in could not start: %s", exc)

    if settings.enable_hsr:
        try:
            account = hsr.login(client, parsed.checkin_cookie, ltuid, parsed.redeem_enabled)
            result = hsr.check_in(client, account)
            results.append(result)
            _log_check_in(result)
        except Exception as exc:
            logger.error("HSR check-in could not start: %s", exc)

    return results
