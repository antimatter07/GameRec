from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class AuthIdentity(Base):
    __tablename__ = "auth_identities"
    __table_args__ = (UniqueConstraint("provider", "provider_sub", name="uq_provider_sub"),)

    id:            Mapped[int]      = mapped_column(primary_key=True)
    user_id:       Mapped[int]      = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider:      Mapped[str]      = mapped_column(String(50),  nullable=False)   # "google", "github", etc.
    provider_sub:  Mapped[str]      = mapped_column(String(255), nullable=False)   # immutable provider user ID
    email_at_link: Mapped[str]      = mapped_column(String(255), nullable=False)   # audit: email at time of linking
    created_at:    Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User", back_populates="auth_identities")
