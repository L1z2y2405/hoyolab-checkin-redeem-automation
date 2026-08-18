"""Application entry points."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from hoyo_auto import __version__
from hoyo_auto.checkin import run_check_in
from hoyo_auto.client import HoyoClient
from hoyo_auto.config import Settings
from hoyo_auto.logging_setup import setup_logging
from hoyo_auto.redeem import run_code_redemption
from hoyo_auto.state import CodeState

logger = logging.getLogger(__name__)


def _state_path(settings: Settings) -> Path:
    return settings.state_dir / "state.json"


def run_once(settings: Settings, *, checkin: bool = True, redeem: bool = True) -> int:
    state = CodeState(_state_path(settings))
    exit_code = 0

    with HoyoClient(timeout=settings.http_timeout) as client:
        if checkin:
            logger.info("Starting daily check-in")
            results = run_check_in(settings, client)
            if any(r.status.value == "failed" for r in results):
                exit_code = 1

        if redeem:
            logger.info("Starting code discovery and redemption")
            run_code_redemption(settings, client, state)

    return exit_code


def run_scheduler(settings: Settings) -> None:
    logger.info(
        "Scheduler started — check-in daily at %02d:%02d, redeem every %d minute(s). Press Ctrl+C to stop.",
        settings.checkin_hour,
        settings.checkin_minute,
        settings.redeem_interval_minutes,
    )

    last_checkin_date: str | None = None
    last_redeem_at: datetime | None = None

    while True:
        now = datetime.now()
        today = now.date().isoformat()
        checkin_due = (
            now.hour == settings.checkin_hour
            and now.minute == settings.checkin_minute
            and last_checkin_date != today
        )
        redeem_due = last_redeem_at is None or now - last_redeem_at >= timedelta(
            minutes=settings.redeem_interval_minutes
        )

        if checkin_due:
            logger.info("Scheduled check-in triggered")
            run_once(settings, checkin=True, redeem=False)
            last_checkin_date = today

        if redeem_due:
            logger.info("Scheduled code redemption triggered")
            run_once(settings, checkin=False, redeem=True)
            last_redeem_at = now

        time.sleep(30)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hoyo-auto",
        description="Personal HoYoLAB automation for Genshin Impact and Honkai: Star Rail.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--env-file",
        default=None,
        help="Path to .env file (default: .env in current directory)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("run", help="Run check-in and code redemption once")

    sub.add_parser("checkin", help="Run daily check-in only")
    sub.add_parser("redeem", help="Discover and redeem codes only")
    sub.add_parser("schedule", help="Run check-in and redemption on a daily schedule")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        settings = Settings.load(args.env_file)
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    setup_logging(settings.log_level)

    if not settings.enable_genshin and not settings.enable_hsr:
        logger.error("Both ENABLE_GENSHIN and ENABLE_HSR are disabled — nothing to do")
        return 2

    if args.command == "run":
        return run_once(settings, checkin=True, redeem=True)
    if args.command == "checkin":
        return run_once(settings, checkin=True, redeem=False)
    if args.command == "redeem":
        return run_once(settings, checkin=False, redeem=True)
    if args.command == "schedule":
        try:
            run_scheduler(settings)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
