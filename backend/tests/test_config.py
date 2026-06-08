import sys
from types import SimpleNamespace

from app import config


def test_load_aws_parameter_values_reads_parameter_path(monkeypatch):
    calls = []

    class FakeSsmClient:
        def get_parameters_by_path(self, **kwargs):
            calls.append(kwargs)
            return {
                "Parameters": [
                    {"Name": "/gamerec/prod/DATABASE_URL", "Value": "postgres-url"},
                    {"Name": "/gamerec/prod/SECRET_KEY", "Value": "secret"},
                    {"Name": "/gamerec/prod/nested/rawg_api_key", "Value": "rawg"},
                ]
            }

    fake_boto3 = SimpleNamespace(client=lambda service, region_name: FakeSsmClient())
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setenv("AWS_SSM_PARAMETER_PATH", "/gamerec/prod")
    monkeypatch.setenv("AWS_REGION", "ap-southeast-1")

    values = config._load_aws_parameter_values()

    assert values == {
        "DATABASE_URL": "postgres-url",
        "SECRET_KEY": "secret",
        "NESTED_RAWG_API_KEY": "rawg",
    }
    assert calls == [
        {
            "Path": "/gamerec/prod",
            "Recursive": True,
            "WithDecryption": True,
        }
    ]


def test_settings_allows_default_secret_outside_production(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    settings = config.Settings(_env_file=None)

    assert settings.SECRET_KEY == "change-me-in-production"


def test_settings_rejects_default_secret_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    try:
        config.Settings(_env_file=None)
    except ValueError as exc:
        assert "SECRET_KEY must be configured for production" in str(exc)
    else:
        raise AssertionError("Expected production settings to reject the default SECRET_KEY")


def test_settings_accepts_configured_secret_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "real-production-secret")
    monkeypatch.setenv("COOKIE_SECURE", "true")

    settings = config.Settings()

    assert settings.SECRET_KEY == "real-production-secret"
    assert settings.COOKIE_SECURE is True


def test_settings_rejects_insecure_cookies_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "real-production-secret")
    monkeypatch.setenv("COOKIE_SECURE", "false")

    try:
        config.Settings(_env_file=None)
    except ValueError as exc:
        assert "COOKIE_SECURE must be true for production" in str(exc)
    else:
        raise AssertionError("Expected production settings to reject insecure cookies")


def test_settings_rejects_insecure_cookies_for_non_local_domain(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("COOKIE_DOMAIN", ".example.com")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173")

    try:
        config.Settings(_env_file=None)
    except ValueError as exc:
        assert "local cookie domains" in str(exc)
    else:
        raise AssertionError("Expected non-local cookie domain to require secure cookies")


def test_settings_rejects_insecure_cookies_for_staging_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.delenv("COOKIE_DOMAIN", raising=False)
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173")

    try:
        config.Settings(_env_file=None)
    except ValueError as exc:
        assert "local or test app environments" in str(exc)
    else:
        raise AssertionError("Expected staging settings to require secure cookies")


def test_settings_rejects_insecure_cookies_for_non_local_origin(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.delenv("COOKIE_DOMAIN", raising=False)
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://app.example.com")

    try:
        config.Settings(_env_file=None)
    except ValueError as exc:
        assert "local allowed origins" in str(exc)
    else:
        raise AssertionError("Expected non-local allowed origin to require secure cookies")


def test_settings_allows_insecure_cookies_for_local_development(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.delenv("COOKIE_DOMAIN", raising=False)
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173")

    settings = config.Settings(_env_file=None)

    assert settings.COOKIE_SECURE is False
