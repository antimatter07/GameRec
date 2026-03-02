import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    BASIC   = "basic"
    PREMIUM = "premium"
    ADMIN   = "admin"


class User(Base):
    __tablename__ = "users"

    id:              Mapped[int]      = mapped_column(primary_key=True)
    email:           Mapped[str]      = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str]      = mapped_column(String(255), nullable=False)
    display_name:    Mapped[str]      = mapped_column(String(100), nullable=True)
    avatar_url:      Mapped[str]      = mapped_column(String(500), nullable=True)
    bio:             Mapped[str]      = mapped_column(Text,        nullable=True)
    role:            Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.BASIC, nullable=False)
    is_active:       Mapped[bool]     = mapped_column(Boolean, default=True, nullable=False)
    created_at:      Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at:      Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    library_entries = relationship("LibraryEntry",   back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")

    # TODO: Add relationship to PremiumRequest model once created (3.2 feature)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
