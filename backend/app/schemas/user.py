from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    email:        EmailStr
    password:     str
    display_name: str | None = None


class UserUpdate(BaseModel):
    display_name: str | None = None
    avatar_url:   str | None = None
    bio:          str | None = None


class UserOut(BaseModel):
    id:           int
    email:        str
    display_name: str | None
    avatar_url:   str | None
    bio:          str | None
    role:         UserRole
    created_at:   datetime

    model_config = {"from_attributes": True}


class UserAdminView(UserOut):
    """Extended view available only to admins."""
    is_active:  bool
    updated_at: datetime
