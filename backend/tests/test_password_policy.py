import pytest

from app.core.password_policy import PasswordPolicyError, validate_password_policy


@pytest.mark.parametrize(
    "password",
    [
        "",
        "        ",
        "Short1!",
        "alllowercase",
        "password123",
    ],
)
def test_validate_password_policy_rejects_weak_passwords(password):
    with pytest.raises(PasswordPolicyError):
        validate_password_policy(password)


def test_validate_password_policy_rejects_email_local_part():
    with pytest.raises(PasswordPolicyError):
        validate_password_policy("Matthew92!", email="matthew@example.com")


def test_validate_password_policy_rejects_display_name_token():
    with pytest.raises(PasswordPolicyError):
        validate_password_policy("Player92!", display_name="Player One")


@pytest.mark.parametrize("password", ["Cinder92", "ember-Map7"])
def test_validate_password_policy_accepts_moderate_passwords(password):
    validate_password_policy(password, email="user@example.com", display_name="Player One")
