from pydantic import BaseModel


class TokenPayload(BaseModel):
    sub:  int   # user ID
    role: str
    exp:  int


class GoogleLoginRequest(BaseModel):
    google_token: str  # access_token from Google implicit flow
