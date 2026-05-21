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
    SESSION_EXPIRE_DAYS: int = 7

    # RAWG API — get your key at rawg.io/apidocs
    RAWG_API_KEY: str
    RAWG_BASE_URL: str
    RAWG_PAGE_SIZE: int = 40
    RAWG_MONTHLY_REQUEST_BUDGET: int = 15000
    RAWG_RECENT_REQUEST_BUDGET: int = 1000
    RAWG_DETAIL_REFRESH_REQUEST_BUDGET: int = 500
    RAWG_DISCOVERY_BUDGET_RATIO: float = 0.9
    RAWG_REJECT_RECHECK_DAYS: int = 90

    # Steam Web API — get your key at steamcommunity.com/dev/apikey
    STEAM_API_KEY: str = ""
    STEAM_API_BASE_URL: str = "https://api.steampowered.com"

    # LLM for premium AI features (Anthropic Claude)
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    AI_PICKS_MODEL: str = "gemini-2.5-flash-lite"
    AI_PICKS_REQUIRE_PREMIUM: bool = False
    AI_PICKS_CACHE_HOURS: int = 24
    AI_PICKS_MAX_CANDIDATES: int = 24
    AI_PICKS_MAX_RESULTS: int = 6
    QUEUE_SUGGESTION_MODEL: str = "gemini-2.5-flash-lite"
    QUEUE_SUGGESTION_REQUIRE_PREMIUM: bool = False

    # SlowAPI rate limits (requests per minute)
    RATE_LIMIT_BASIC: str = "30/minute"
    RATE_LIMIT_PREMIUM: str = "100/minute"
    RATE_LIMIT_ADMIN: str = "200/minute"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # CORS
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]


settings = Settings()
