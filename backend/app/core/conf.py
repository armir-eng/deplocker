import os
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Postgres DB parameters
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    TEST_DB: str

    # Frontend URL
    # Where used, the frontend URL is resolved based on the application's environment (through ENVIRONMENT variable)
    # Also, both of them are passed hand-in-hand as allowed origins in the CORS configuration.
    ENVIRONMENT: Literal["dev", "production"]
    DEV_FRONTEND_URL: str
    PROD_FRONTEND_URL: str

    # Public URL
    # This service's own externally reachable origin, resolved the same way as the
    # frontend URL. OAuth2 providers redirect back to it, so it must match what is
    # registered with each provider.
    DEV_PUBLIC_URL: str = "http://localhost:8080"
    PROD_PUBLIC_URL: str

    # JWT configuration parameters
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRES_MINUTES: int

    # RabbitMQ configuration parameters
    RABBITMQ_DEFAULT_USER: str
    RABBITMQ_DEFAULT_PASS: str
    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_DEFAULT_VHOST: str

    # Redis configuration parameters
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    # Email service parameters
    SMTP_HOST: str
    SMTP_PORT: int
    SENDER_EMAIL_ADDRESS: str
    EMAIL_HOST_PASSWORD: str

    # Google OAuth2 configuration parameters
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_AUTH_URL: str
    GOOGLE_TOKEN_URL: str
    GOOGLE_USER_INFO_URL: str

    # GitHub OAuth2 configuration parameters
    GITHUB_CLIENT_ID: str
    GITHUB_CLIENT_SECRET: str
    GITHUB_AUTH_URL: str
    GITHUB_TOKEN_URL: str
    GITHUB_USER_INFO_URL: str
    GITHUB_USER_EMAILS_URL: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def FRONTEND_URL(self) -> str:
        """Root frontend URL for the active environment (single source of truth)."""
        return (
            self.PROD_FRONTEND_URL
            if self.ENVIRONMENT == "production"
            else self.DEV_FRONTEND_URL
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def PUBLIC_URL(self) -> str:
        """Own root URL for the active environment (single source of truth)."""
        return (
            self.PROD_PUBLIC_URL
            if self.ENVIRONMENT == "production"
            else self.DEV_PUBLIC_URL
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        return f"{self.PUBLIC_URL}/auth/google/callback"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def GITHUB_REDIRECT_URI(self) -> str:
        return f"{self.PUBLIC_URL}/auth/github/callback"

    # Real environment variables win over the file; the file is a local-dev
    # convenience and is absent wherever the platform injects secrets directly.
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"), env_file_encoding="utf-8"
    )


settings = Settings()
