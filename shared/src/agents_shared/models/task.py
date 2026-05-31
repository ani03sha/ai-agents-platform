"""Cross-service enums for task lifecycle and agent roles.

These live in the shared library because both the API (which sets/reads status)
and the worker (which transitions it) must agree on the exact string values.

They are persisted in PostgreSQL and must never drift between services.
"""

from enum import StrEnum


class TaskStatus(StrEnum):
    PENDING = "PENDING"
    PLANNING = "PLANNING"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    @property
    def is_terminal(self) -> bool:
        return self in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED)


class AgentRole(StrEnum):
    PLANNER = "planner"
    RESEARCH = "research"
    CODE = "code"
    WRITING = "writing"
    CRITIC = "critic"
