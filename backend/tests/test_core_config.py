import pytest
from pydantic import ValidationError

from backend.app.core.config import Settings


def test_cors_requires_explicit_origins_and_https_off_loopback():
    configured = Settings(
        DEBUG=True,
        CORS_ORIGINS="http://localhost:5173/,https://dashboard.example.org",
    )
    assert configured.CORS_ORIGINS == ["http://localhost:5173", "https://dashboard.example.org"]

    with pytest.raises(ValidationError, match="wildcards are not allowed"):
        Settings(DEBUG=True, CORS_ORIGINS="*")
    with pytest.raises(ValidationError, match="must use HTTPS"):
        Settings(DEBUG=True, CORS_ORIGINS="http://dashboard.example.org")
