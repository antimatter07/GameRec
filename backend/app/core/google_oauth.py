import httpx

from app.config import settings

GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleTokenError(Exception):
    pass


def verify_google_access_token(access_token: str) -> dict:
    """
    Call Google's userinfo endpoint to validate an access_token and return user claims.
    Returns dict with: sub, email, email_verified, name, picture.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise GoogleTokenError("Google OAuth is not configured on this server")
    try:
        response = httpx.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise GoogleTokenError(f"Google rejected the token: {e.response.status_code}") from e
    except httpx.HTTPError as e:
        raise GoogleTokenError(f"Could not reach Google: {e}") from e

    claims = response.json()
    if not claims.get("email_verified"):
        raise GoogleTokenError("Google account email is not verified")
    if not claims.get("sub"):
        raise GoogleTokenError("Missing user ID in Google response")
    return claims
