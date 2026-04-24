from pydantic import BaseModel


class Token(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class TokenPayload(BaseModel):
    sub:  int   # user ID
    role: str
    exp:  int


class GoogleLoginRequest(BaseModel):
    google_token: str  # access_token from Google implicit flow
