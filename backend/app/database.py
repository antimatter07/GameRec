from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

if settings.APP_RUNTIME == "lambda":
    engine_kwargs["poolclass"] = NullPool

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — yields a DB session and ensures it's closed afterward."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
