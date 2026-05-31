from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    service_name: str = "agent-gateway"
    debug: bool = False

    # Postgres - task state, step log, approvals, audit, api keys
    database_uri: str = "postgresql://agents:agents_dev_password@localhost:5633/agents"

    # Redis - live SSE stream relay (pub/sub) + KV cache
    redis_url: str = "redis://localhost:6390"

    # Redpanda - durable task queue
    kafka_brokers: str = "localhost:9093"

    # Auth
    api_keys: str = "dev-key-1,dev-key-2"  # comma separated; replace with DB in prod
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiry_minutes: int = 15
    jwt_refresh_expiry_days: int = 7

    # Observability
    otlp_endpoint: str = "http://localhost:4318"
    tracing_enabled: bool = True

settings = Settings()