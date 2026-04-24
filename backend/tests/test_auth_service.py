"""
Unit tests for app/services/auth_service.py.
DB and Redis are mocked — testing authentication logic only.
"""
from unittest.mock import MagicMock, patch

from app.core.security import hash_password
from app.models.user import User, UserRole
from app.services.auth_service import authenticate_user, issue_tokens


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


# ── issue_tokens ───────────────────────────────────────────────────────────────

def test_issue_tokens_returns_expected_keys():
    user = _make_user()
    with patch("app.services.auth_service.redis_client"):
        result = issue_tokens(user)

    assert "access_token" in result
    assert "refresh_token" in result
    assert result["token_type"] == "bearer"


def test_issue_tokens_stores_refresh_token_in_redis():
    user = _make_user()
    with patch("app.services.auth_service.redis_client") as mock_redis:
        issue_tokens(user)

    mock_redis.setex.assert_called_once()
    key_used = mock_redis.setex.call_args[0][0]
    assert key_used == f"refresh:{user.id}"


def test_issue_tokens_access_and_refresh_are_different():
    user = _make_user()
    with patch("app.services.auth_service.redis_client"):
        result = issue_tokens(user)

    assert result["access_token"] != result["refresh_token"]
