"""Credit service unit tests."""

import pytest
from app.services.credit import InsufficientCreditsError


def test_insufficient_credits_is_402():
    exc = InsufficientCreditsError(balance=3, required=10)
    assert exc.status_code == 402


def test_insufficient_credits_detail_message():
    exc = InsufficientCreditsError(balance=3, required=10)
    assert "3" in exc.detail
    assert "10" in exc.detail


def test_insufficient_credits_zero_balance():
    exc = InsufficientCreditsError(balance=0, required=2)
    assert exc.status_code == 402
    assert "0" in exc.detail
