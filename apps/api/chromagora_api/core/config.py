"""Application configuration from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Chromagora OS API settings."""

    # API
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    chromagora_env: str = "development"
    chromagora_tenant_id: str = ""
    version: str = "0.1.0"

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_access_token: str = ""
    database_url: str = ""

    # OpenRouter
    openrouter_api_key: str = ""

    # Features
    enable_vector_memory: bool = False
    enable_real_email_sending: bool = False

    # Auth
    api_keys: str = ""
    enforce_auth: bool = False

    # Security
    allowed_origins: str = "*"
    rate_limit_per_minute: int = 60
    enforce_rate_limit: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
