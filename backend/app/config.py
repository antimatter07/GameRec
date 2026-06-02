import os
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _load_aws_parameter_values() -> dict[str, Any]:
    parameter_path = os.environ.get("AWS_SSM_PARAMETER_PATH")
    if not parameter_path:
        return {}

    import boto3

    normalized_path = "/" + parameter_path.strip("/")
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    client = boto3.client("ssm", region_name=region)
    values: dict[str, Any] = {}
    next_token: str | None = None

    while True:
        kwargs: dict[str, Any] = {
            "Path": normalized_path,
            "Recursive": True,
            "WithDecryption": True,
        }
        if next_token:
            kwargs["NextToken"] = next_token

        response = client.get_parameters_by_path(**kwargs)
        for parameter in response.get("Parameters", []):
            name = parameter["Name"]
            key = name.removeprefix(normalized_path).strip("/").replace("/", "_").upper()
            if key:
                values[key] = parameter.get("Value", "")

        next_token = response.get("NextToken")
        if not next_token:
            return values


_AWS_PARAMETER_VALUES = _load_aws_parameter_values()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_ENV: str = "development"
    APP_RUNTIME: str = "local"  # local | lambda | fargate
    SECRET_KEY: str = _AWS_PARAMETER_VALUES.get("SECRET_KEY", "change-me-in-production")
    TASK_BACKEND: str = "celery"  # celery | sqs
    KV_BACKEND: str = "redis"  # redis | dynamodb
    AWS_SSM_PARAMETER_PATH: str = ""

    # Database (Supabase PostgreSQL connection string)
    DATABASE_URL: str = _AWS_PARAMETER_VALUES.get("DATABASE_URL", "")

    # Redis (used by Celery broker + result backend, and for token blacklisting)
    REDIS_URL: str = "redis://localhost:6379/0"

    # AWS deployment
    AWS_REGION: str = "ap-southeast-1"
    DYNAMODB_KV_TABLE: str = ""
    SQS_RECOMMENDATION_QUEUE_URL: str = ""
    SQS_HLTB_QUEUE_URL: str = ""
    SQS_AI_QUEUE_URL: str = ""
    SQS_RAWG_QUEUE_URL: str = ""
    ECS_CLUSTER_ARN: str = ""
    ECS_RAWG_TASK_DEFINITION_ARN: str = ""
    ECS_RAWG_CONTAINER_NAME: str = "rawg"
    ECS_SUBNET_IDS: str | list[str] = []
    ECS_SECURITY_GROUP_IDS: str | list[str] = []

    # JWT
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_EXPIRE_DAYS: int = 7

    # RAWG API — get your key at rawg.io/apidocs
    RAWG_API_KEY: str = _AWS_PARAMETER_VALUES.get("RAWG_API_KEY", "")
    RAWG_BASE_URL: str = _AWS_PARAMETER_VALUES.get("RAWG_BASE_URL", "")
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
    ANTHROPIC_API_KEY: str = _AWS_PARAMETER_VALUES.get("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY: str = _AWS_PARAMETER_VALUES.get("GEMINI_API_KEY", "")
    AI_PICKS_MODEL: str = "gemini-2.5-flash-lite"
    AI_PICKS_REQUIRE_PREMIUM: bool = False
    AI_PICKS_CACHE_HOURS: int = 24
    AI_PICKS_MAX_CANDIDATES: int = 30
    AI_PICKS_MAX_RESULTS: int = 6
    QUEUE_SUGGESTION_MODEL: str = "gemini-2.5-flash-lite"
    QUEUE_SUGGESTION_REQUIRE_PREMIUM: bool = False

    # SlowAPI rate limits (requests per minute)
    RATE_LIMIT_BASIC: str = "30/minute"
    RATE_LIMIT_PREMIUM: str = "100/minute"
    RATE_LIMIT_ADMIN: str = "200/minute"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = _AWS_PARAMETER_VALUES.get("GOOGLE_CLIENT_ID", "")

    # CORS
    ALLOWED_ORIGINS: str | list[str] = ["http://localhost:5173"]

    # Cookies
    COOKIE_DOMAIN: str = ""
    COOKIE_SAMESITE: str = "lax"

    @field_validator("ALLOWED_ORIGINS", "ECS_SUBNET_IDS", "ECS_SECURITY_GROUP_IDS", mode="before")
    @classmethod
    def _parse_string_list(cls, value: Any) -> Any:
        if isinstance(value, str) and not value:
            return []
        if isinstance(value, str) and not value.lstrip().startswith("["):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value


settings = Settings()
