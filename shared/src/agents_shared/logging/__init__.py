"""Structured logging configuration shared by every service.

Console renderer in debug (readable locally), JSON in production (machine-parseable
for log aggregation). Both bind contextvars so a request_id / task_id set once is
attached to every subsequent log line in that context.
"""

import structlog


def configure_logging(debug: bool = False) -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.ConsoleRenderer()
            if debug
            else structlog.dev.JSONRenderer(),
        ]
    )
