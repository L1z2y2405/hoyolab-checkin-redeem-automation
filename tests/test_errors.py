"""Tests for retcode classification."""

from hoyo_auto.errors import FailureKind, classify_retcode


def test_success_retcode():
    kind, message, cache = classify_retcode(0)
    assert kind == FailureKind.SUCCESS
    assert cache is True


def test_expired_code_is_cached():
    kind, _, cache = classify_retcode(-2001)
    assert kind == FailureKind.EXPIRED
    assert cache is True


def test_already_redeemed_is_cached():
    kind, _, cache = classify_retcode(-2017)
    assert kind == FailureKind.ALREADY_DONE
    assert cache is True


def test_busy_api_is_temporary():
    kind, _, cache = classify_retcode(-1048)
    assert kind == FailureKind.TEMPORARY
    assert cache is False


def test_auth_failure_is_not_cached():
    kind, _, cache = classify_retcode(-100)
    assert kind == FailureKind.AUTH
    assert cache is False
