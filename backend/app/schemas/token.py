from pydantic import BaseModel


class TokenPayload(BaseModel):
    """JWT payload schema containing subject, role, and token type claims."""
    sub:  int   # user ID
    role: str
    exp:  int


class GoogleLoginRequest(BaseModel):
    """Request schema carrying a Google OAuth token."""
    google_token: str  # access_token from Google implicit flow
