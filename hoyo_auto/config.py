"""Load settings from environment variables."""

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
import os


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_bool_optional(name: str) -> bool | None:
    raw = os.getenv(name)
    if raw is None:
        return None
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    cookie: str
    enable_genshin: bool
    enable_hsr_checkin: bool
    enable_hsr_redeem: bool
    state_dir: Path
    log_level: str
    checkin_hour: int
    checkin_minute: int
    redeem_interval_minutes: int
    http_timeout: float
    redeem_delay_seconds: float

    @classmethod
    def load(cls, env_file: str | None = None) -> "Settings":
        load_dotenv(env_file)

        cookie = os.getenv("HOYOLAB_COOKIE", "").strip()
        if not cookie:
            raise ValueError(
                "HOYOLAB_COOKIE is required. Copy .env.example to .env and set your cookie."
            )

        state_dir = Path(os.getenv("STATE_DIR", "data"))
        checkin_hour = int(os.getenv("CHECKIN_HOUR", "0"))
        checkin_minute = int(os.getenv("CHECKIN_MINUTE", "5"))
        redeem_interval = int(os.getenv("REDEEM_INTERVAL_MINUTES", "15"))

        if not 0 <= checkin_hour <= 23:
            raise ValueError("CHECKIN_HOUR must be between 0 and 23")
        if not 0 <= checkin_minute <= 59:
            raise ValueError("CHECKIN_MINUTE must be between 0 and 59")
        if redeem_interval < 1:
            raise ValueError("REDEEM_INTERVAL_MINUTES must be at least 1")

        hsr_master = _env_bool("ENABLE_HSR", True)
        hsr_checkin = _env_bool_optional("ENABLE_HSR_CHECKIN")
        hsr_redeem = _env_bool_optional("ENABLE_HSR_REDEEM")

        return cls(
            cookie=cookie,
            enable_genshin=_env_bool("ENABLE_GENSHIN", True),
            enable_hsr_checkin=hsr_master if hsr_checkin is None else hsr_checkin,
            enable_hsr_redeem=hsr_master if hsr_redeem is None else hsr_redeem,
            state_dir=state_dir,
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            checkin_hour=checkin_hour,
            checkin_minute=checkin_minute,
            redeem_interval_minutes=redeem_interval,
            http_timeout=float(os.getenv("HTTP_TIMEOUT", "30")),
            redeem_delay_seconds=float(os.getenv("REDEEM_DELAY_SECONDS", "6")),
        )
