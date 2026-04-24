from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "change-me-in-production"

    # Database (Supabase PostgreSQL connection string)
    DATABASE_URL: str 

    # Redis (used by Celery broker + result backend, and for token blacklisting)
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # RAWG API — get your key at rawg.io/apidocs
    RAWG_API_KEY: str
    RAWG_BASE_URL: str

    # LLM for premium AI features (Anthropic Claude)
    ANTHROPIC_API_KEY: str = ""

    # SlowAPI rate limits (requests per minute)
    RATE_LIMIT_BASIC: str = "30/minute"
    RATE_LIMIT_PREMIUM: str = "100/minute"
    RATE_LIMIT_ADMIN: str = "200/minute"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()
