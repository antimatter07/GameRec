"""
Unit tests for app/services/auth_service.py.
DB and the key/value store are mocked — testing authentication, revocation, and JWT lookup logic.
"""
from unittest.mock import MagicMock, patch

from app.core.security import create_auth_token, hash_password
from app.models.user import User, UserRole
from app.services.auth_service import (
    _revoked_token_key,
    authenticate_user,
    generate_csrf_token,
    get_user_for_token,
    is_auth_token_revoked,
    revoke_auth_token,
)


def _make_user(password="password123", is_active=True, role=UserRole.BASIC) -> User:
    user = MagicMock(spec=User)
    user.id = 1
    user.email = "test@example.com"
    user.hashed_password = hash_password(password)
    user.is_active = is_active
    user.role = role
    return user


# ── authenticate_user ──────────────────────────────────────────────────────────

def test_authenticate_user_success():
    db = MagicMock()
    user = _make_user(password="password123")
    db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(db, "test@example.com", "password123")

    assert result == user


def test_authenticate_user_wrong_password_returns_none():
    db = MagicMock()
    user = _make_user(password="correctpassword")
    db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(db, "test@example.com", "wrongpassword")

    assert result is None


def test_authenticate_user_not_found_returns_none():
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    result = authenticate_user(db, "nobody@example.com", "password")

    assert result is None


def test_authenticate_user_inactive_account_returns_none():
    db = MagicMock()
    user = _make_user(is_active=False)
    db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(db, "test@example.com", "password123")

    assert result is None


def test_authenticate_user_without_password_returns_none():
    db = MagicMock()
    user = _make_user()
    user.hashed_password = None
    db.query.return_value.filter.return_value.first.return_value = user

    result = authenticate_user(db, "test@example.com", "password123")

    assert result is None


# ── csrf helpers ───────────────────────────────────────────────────────────────

def test_generate_csrf_token_is_non_empty():
    token = generate_csrf_token()

    assert isinstance(token, str)
    assert len(token) > 20


# ── revocation helpers ─────────────────────────────────────────────────────────

def test_revoke_auth_token_stores_token_jti_in_redis():
    token = create_auth_token(user_id=1, role="basic")
    with patch("app.services.auth_service.kv_store") as mock_kv:
        revoke_auth_token(token)

    mock_kv.set_text.assert_called_once()
    key_used = mock_kv.set_text.call_args[0][0]
    assert key_used.startswith(_revoked_token_key(""))


def test_is_auth_token_revoked_reads_redis():
    with patch("app.services.auth_service.kv_store") as mock_kv:
        mock_kv.exists.return_value = True
        result = is_auth_token_revoked({"jti": "abc123"})

    assert result is True


# ── JWT lookup ─────────────────────────────────────────────────────────────────

def test_get_user_for_token_returns_user_when_valid():
    user = _make_user()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    token = create_auth_token(user_id=user.id, role="basic")

    with patch("app.services.auth_service.kv_store") as mock_kv:
        mock_kv.exists.return_value = False
        result = get_user_for_token(db, token)

    assert result == user


def test_get_user_for_token_returns_none_when_revoked():
    user = _make_user()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = user
    token = create_auth_token(user_id=user.id, role="basic")

    with patch("app.services.auth_service.kv_store") as mock_kv:
        mock_kv.exists.return_value = True
        result = get_user_for_token(db, token)

    assert result is None


def test_get_user_for_token_returns_none_for_invalid_token():
    db = MagicMock()
    with patch("app.services.auth_service.kv_store"):
        result = get_user_for_token(db, "not.a.valid.token")

    assert result is None
