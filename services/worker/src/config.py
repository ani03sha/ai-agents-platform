from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ENV_FILE = Path(__file__).parent.parent.parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(_ENV_FILE), extra="ignore")

    service_name: str = "agent-worker"
    debug: bool = False

    # Redpanda — durable task queue (consumed here)
    kafka_brokers: str = "localhost:9093"
    consumer_group: str = "agent-workers"

    # PostgreSQL — task state + append-only step log (the checkpoint)
    database_url: str = "postgresql://agents:agents_dev_password@localhost:5633/agents"

    # Redis — publishes reasoning steps to the SSE relay
    redis_url: str = "redis://localhost:6390"

    # Qdrant — long-term agent memory
    qdrant_host: str = "localhost"
    qdrant_port: int = 6353
    qdrant_memory_collection: str = "agent_memory"

    # Ollama — LLM + embeddings
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:14b"
    embedding_model: str = "nomic-embed-text"

    # Observability
    health_port: int = 8011
    otlp_endpoint: str = "http://localhost:4318"
    tracing_enabled: bool = True


settings = Settings()
