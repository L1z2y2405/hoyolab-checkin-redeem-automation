"""Discover and redeem codes for enabled games."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass

from hoyo_auto.auth import extract_ltuid, parse_cookie
from hoyo_auto.client import HoyoClient
from hoyo_auto.config import Settings
from hoyo_auto.games import genshin, hsr
from hoyo_auto.games.base import RedeemResult
from hoyo_auto.state import CodeState

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GameRedeemModule:
    key: str
    name: str
    fetch_codes: Callable
    login: Callable
    redeem_with_delay: Callable


GAME_MODULES = {
    "genshin": GameRedeemModule(
        key="genshin",
        name="Genshin Impact",
        fetch_codes=genshin.fetch_codes,
        login=genshin.login,
        redeem_with_delay=genshin.redeem_with_delay,
    ),
    "hsr": GameRedeemModule(
        key="hsr",
        name="Honkai: Star Rail",
        fetch_codes=hsr.fetch_codes,
        login=hsr.login,
        redeem_with_delay=hsr.redeem_with_delay,
    ),
}


def _normalize_codes(entries: list[dict]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for entry in entries:
        code = str(entry.get("code", "")).upper().strip()
        if code and code not in seen:
            seen.add(code)
            normalized.append(code)
    return normalized


def _log_redeem(module: GameRedeemModule, result: RedeemResult) -> None:
    if result.success:
        logger.info("[%s] redeemed %s", module.name, result.code)
    elif result.cache_code:
        logger.info("[%s] %s — %s (will not retry)", module.name, result.code, result.message)
    else:
        logger.warning("[%s] %s — %s (may retry later)", module.name, result.code, result.message)


def run_code_redemption(
    settings: Settings,
    client: HoyoClient,
    state: CodeState,
) -> list[RedeemResult]:
    parsed = parse_cookie(settings.cookie)
    ltuid = extract_ltuid(settings.cookie)
    all_results: list[RedeemResult] = []

    enabled_keys = []
    if settings.enable_genshin:
        enabled_keys.append("genshin")
    if settings.enable_hsr:
        enabled_keys.append("hsr")

    for key in enabled_keys:
        module = GAME_MODULES[key]
        discovered_entries = module.fetch_codes(client)
        discovered = _normalize_codes(discovered_entries)

        if not discovered:
            logger.debug("%s: no active codes discovered", module.name)
            continue

        if state.bootstrap_if_empty(key, discovered):
            continue

        new_codes = state.filter_new(key, discovered)
        if not new_codes:
            logger.debug("%s: no new codes to redeem", module.name)
            continue

        logger.info("%s: found %d new code(s) to redeem", module.name, len(new_codes))

        try:
            account = module.login(client, parsed.checkin_cookie, ltuid, parsed.redeem_enabled)
        except Exception as exc:
            logger.error("%s: could not resolve account for redemption: %s", module.name, exc)
            continue

        results = module.redeem_with_delay(
            client,
            account,
            new_codes,
            settings.redeem_delay_seconds,
        )

        cached_now: set[str] = set()
        for result in results:
            all_results.append(result)
            _log_redeem(module, result)
            if result.cache_code:
                cached_now.add(result.code)

        # Cache permanently processed codes; leave temporary failures for retry.
        state.add_codes(key, cached_now)

    return all_results
