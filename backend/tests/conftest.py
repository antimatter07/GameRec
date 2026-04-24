import os

# Must be set before any app module is imported (settings = Settings() runs at import time)
os.environ.setdefault("DATABASE_URL", "postgresql://user:password@localhost/testdb")
os.environ.setdefault("RAWG_API_KEY", "dummy-key-for-tests")
os.environ.setdefault("RAWG_BASE_URL", "https://api.rawg.io/api")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only")
