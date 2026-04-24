from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.config import settings


class GoogleTokenError(Exception):
    pass


def verify_google_id_token(token: str) -> dict:
    """Verify a Google ID token and return its claims, or raise GoogleTokenError."""
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleTokenError("Google OAuth is not configured on this server")
    try:
        claims = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
        )
    except ValueError as e:
        raise GoogleTokenError(f"Invalid Google token: {e}") from e

    if claims.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        raise GoogleTokenError("Token has wrong issuer")
    if not claims.get("email_verified"):
        raise GoogleTokenError("Google account email is not verified")

    # claims contains: sub, email, email_verified, name, picture, aud, iss, exp
    return claims
