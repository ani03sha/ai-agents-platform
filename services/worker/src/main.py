import asyncio
from unittest import async_case

import structlog
import uvicorn

from agents_shared.logging import configure_logging

from .config import settings
from .health import app as health_app
from .tracing import setup_tracing

configure_logging(settings.debug)
log = structlog.get_logger()


async def _serve_health() -> None:
    """Run the /health + /metrics sidecar so the process is observable."""
    config = uvicorn.Config(
        health_app,
        host="0.0.0.0",
        port=settings.health_port,
        log_level="warning",  # quiet; this server is not the interesting part
    )

    server = uvicorn.Server(config)
    await server.serve()


async def _run_consumer() -> None:
    """Stub. Phase 3 replaces this with TaskConsumer(...).run() — consuming
    agent.task.requested / agent.task.resumed, running the ReAct loop, and
    checkpointing each step to PostgreSQL."""
    log.info("worker.consumer.idle", note="real consumer wired in Phase 3")
    while True:
        await asyncio.sleep(30)
        log.debug("worker.heartbeat")


async def main() -> None:
    if settings.tracing_enabled:
        setup_tracing(health_app, settings.service_name, settings.otlp_endpoint)
    log.info(
        "worker.starting",
        service=settings.service_name,
        health_port=settings.health_port,
    )
    await asyncio.gather(_serve_health(), _run_consumer())


if __name__ == "__main__":
    asyncio.run(main())
