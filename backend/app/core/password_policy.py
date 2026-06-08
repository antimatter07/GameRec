import re


MIN_PASSWORD_LENGTH = 8
PASSWORD_POLICY_MESSAGE = (
    "Password must be at least 8 characters, include at least 3 of lowercase letters, "
    "uppercase letters, numbers, and symbols, and not include your email or display name."
)


class PasswordPolicyError(ValueError):
    """Raised when a password does not meet the account password policy."""


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.lower())


def _display_name_tokens(display_name: str | None) -> list[str]:
    if not display_name:
        return []
    return [token for token in re.findall(r"[a-z0-9]+", display_name.lower()) if len(token) >= 3]


def validate_password_policy(
    password: str,
    *,
    email: str | None = None,
    display_name: str | None = None,
) -> None:
    """Validate a new local-account password."""
    if not password or not password.strip():
        raise PasswordPolicyError("Password cannot be empty.")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise PasswordPolicyError(PASSWORD_POLICY_MESSAGE)

    class_count = sum(
        (
            any(char.islower() for char in password),
            any(char.isupper() for char in password),
            any(char.isdigit() for char in password),
            any(not char.isalnum() for char in password),
        )
    )
    if class_count < 3:
        raise PasswordPolicyError(PASSWORD_POLICY_MESSAGE)

    compact_password = _compact(password)
    if email:
        email_local_part = _compact(email.split("@", 1)[0])
        if len(email_local_part) >= 3 and email_local_part in compact_password:
            raise PasswordPolicyError(PASSWORD_POLICY_MESSAGE)

    for token in _display_name_tokens(display_name):
        if token in compact_password:
            raise PasswordPolicyError(PASSWORD_POLICY_MESSAGE)
