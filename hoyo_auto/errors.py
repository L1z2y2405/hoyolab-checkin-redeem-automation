"""HoYoLAB API error classification."""

from enum import Enum


class FailureKind(str, Enum):
    SUCCESS = "success"
    ALREADY_DONE = "already_done"
    EXPIRED = "expired"
    INVALID = "invalid"
    AUTH = "auth"
    TEMPORARY = "temporary"
    UNKNOWN = "unknown"


# retcode -> (human message, whether the code should be cached as permanently processed)
RETCODE_INFO: dict[int, tuple[str, bool]] = {
    1009: ("The account does not exist", False),
    -100: ("Cookie is invalid or expired", False),
    -10001: ("Cookie is invalid or expired", False),
    -10101: ("Daily account lookup limit reached", True),
    -1048: ("API is busy, try again later", False),
    -1071: ("Cookie is invalid or expired", False),
    -2001: ("Code has expired", True),
    -2003: ("Code is invalid", True),
    -2016: ("Redemption cooldown active", False),
    -2017: ("Code already redeemed on this account", True),
}

CAPTCHA_RETCODES = {10035, 5003, 10041, 1034}


def classify_retcode(retcode: int) -> tuple[FailureKind, str, bool]:
    """Return (kind, message, should_cache_code)."""
    if retcode == 0:
        return FailureKind.SUCCESS, "OK", True

    if retcode in CAPTCHA_RETCODES:
        return (
            FailureKind.AUTH,
            "Captcha required — visit HoYoLAB game records to solve it",
            False,
        )

    if retcode in RETCODE_INFO:
        message, cache = RETCODE_INFO[retcode]
        if retcode in (-2001, -2003):
            kind = FailureKind.EXPIRED if retcode == -2001 else FailureKind.INVALID
        elif retcode == -2017:
            kind = FailureKind.ALREADY_DONE
        elif retcode in (-100, -10001, -1071):
            kind = FailureKind.AUTH
        elif retcode == -1048:
            kind = FailureKind.TEMPORARY
        else:
            kind = FailureKind.UNKNOWN
        return kind, message, cache

    return FailureKind.UNKNOWN, f"Unexpected API response (retcode={retcode})", False
