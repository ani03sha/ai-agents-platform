from contextlib import asynccontextmanager

import structlog
import uvicorn
from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from agents_shared.logging import configure_logging

from .api.middleware import LoggingMiddleware
from .api.v1.routes import auth, health
from .config import settings
from .tracing import setup_tracing

configure_logging(settings.debug)
log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("service.starting", service=settings.service_name)
    # Wires adapters here: TaskStore (Postgres), EventBus (Redpanda producer),
    # StepSubscriber (Redis). The task/stream/approval routes attach then.
    yield
    log.info("service.stopping", service=settings.service_name)


app = FastAPI(title="Agent Gateway", version="0.1.0", lifespan=lifespan)
app.add_middleware(LoggingMiddleware)
Instrumentator().instrument(app).expose(app, endpoint="/metrics")
if settings.tracing_enabled:
    setup_tracing(app, settings.service_name, settings.otlp_endpoint)
app.include_router(health.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8010, reload=settings.debug)
