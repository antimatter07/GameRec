"""
Unit tests for app/core/security.py.
No DB or external dependencies — purely testing JWT and password hashing logic.
"""
import pytest
from fastapi import HTTPException

from app.core.security import (
    create_auth_token,
    decode_auth_token,
    hash_password,
    verify_password,
)


# ── Password hashing ───────────────────────────────────────────────────────────

def test_hash_and_verify_correct_password():
    hashed = hash_password("mysecretpassword")
    assert verify_password("mysecretpassword", hashed)


def test_wrong_password_fails_verification():
    hashed = hash_password("mysecretpassword")
    assert not verify_password("wrongpassword", hashed)


def test_empty_password_does_not_match_non_empty_hash():
    hashed = hash_password("somepassword")
    assert not verify_password("", hashed)


def test_hashes_are_unique_per_call():
    # bcrypt generates a new salt each time
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2
    assert verify_password("same", h1)
    assert verify_password("same", h2)


# ── Auth token ────────────────────────────────────────────────────────────────

def test_auth_token_roundtrip():
    token = create_auth_token(user_id=42, role="basic")
    payload = decode_auth_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "basic"
    assert payload["type"] == "auth"
    assert "jti" in payload


def test_auth_token_contains_expiry():
    token = create_auth_token(user_id=1, role="basic")
    payload = decode_auth_token(token)
    assert "exp" in payload


def test_invalid_token_raises_401():
    with pytest.raises(HTTPException) as exc:
        decode_auth_token("not.a.valid.token")
    assert exc.value.status_code == 401


def test_tampered_token_raises_401():
    token = create_auth_token(user_id=1, role="basic")
    tampered = token[:-10] + "XXXXXXXXXX"
    with pytest.raises(HTTPException) as exc:
        decode_auth_token(tampered)
    assert exc.value.status_code == 401


def test_different_user_ids_produce_different_tokens():
    t1 = create_auth_token(user_id=1, role="basic")
    t2 = create_auth_token(user_id=2, role="basic")
    assert t1 != t2


def test_same_user_id_produce_different_tokens_due_to_jti():
    t1 = create_auth_token(user_id=1, role="basic")
    t2 = create_auth_token(user_id=1, role="basic")
    assert t1 != t2
