"""Auth service unit tests — no database required."""

import pytest
from app.services.auth import hash_password, verify_password, create_access_token, decode_token


def test_password_hashing():
    plain = "SuperSecret123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong", hashed)


def test_access_token_round_trip():
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    token = create_access_token(user_id)
    payload = decode_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_invalid_token_raises():
    with pytest.raises(Exception):
        decode_token("not.a.valid.token")
