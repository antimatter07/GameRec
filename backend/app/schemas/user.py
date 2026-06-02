from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Request schema for local account registration."""
    email:        EmailStr
    password:     str
    display_name: str | None = None


class UserUpdate(BaseModel):
    """Request schema for updating profile fields on the current user."""
    display_name: str | None = None
    avatar_url:   str | None = None
    bio:          str | None = None


class UserOut(BaseModel):
    """Public user response schema."""
    id:           int
    email:        str
    display_name: str | None
    avatar_url:   str | None
    bio:          str | None
    role:         UserRole
    created_at:   datetime

    model_config = {"from_attributes": True}


class UserAdminView(UserOut):
    """Admin user response schema including operational fields."""
    is_active:  bool
    updated_at: datetime
