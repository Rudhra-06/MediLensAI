"""Core configuration for MediLens AI backend."""
import ipaddress
from typing import List, Union
from urllib.parse import urlsplit
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    APP_NAME: str = "MediLens AI"
    APP_VERSION: str = "0.1.0"
    API_PREFIX: str = "/api"
    MEDILENS_ENV: str = "development"
    DEBUG: bool = True
    LOCAL_PROVIDER_DEMO_ENABLED: bool = False

    # Server configuration
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # CORS origins: comma-separated string or list of strings
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            origins = [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            origins = [str(i).strip() for i in v if str(i).strip()]
        else:
            origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

        normalized = []
        for origin in origins:
            try:
                parsed = urlsplit(origin)
                hostname = parsed.hostname
                _ = parsed.port  # Validate malformed/out-of-range ports.
            except ValueError as exc:
                raise ValueError("CORS origins must be valid explicit HTTP(S) origins.") from exc
            if (
                origin == "*"
                or parsed.scheme not in {"http", "https"}
                or not hostname
                or parsed.username is not None
                or parsed.password is not None
                or parsed.path not in {"", "/"}
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("CORS origins must be valid explicit HTTP(S) origins; wildcards are not allowed.")
            if parsed.scheme == "http":
                try:
                    is_loopback = ipaddress.ip_address(hostname).is_loopback
                except ValueError:
                    is_loopback = hostname.casefold() == "localhost"
                if not is_loopback:
                    raise ValueError("Non-loopback CORS origins must use HTTPS.")
            normalized.append(origin.rstrip("/"))
        return list(dict.fromkeys(normalized))

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
