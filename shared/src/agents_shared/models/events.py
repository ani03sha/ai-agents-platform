"""Event schemas exchanged over Redpanda, plus the topic names.

Redpanda carries durable "task lifecycle" events only. Live reasoning steps are streamed over Redis pub/sub (not here).
Delivery is at-least-once; consumers must be idempotent (see the UNIQUE (task_id, idx) constraint on task_steps).
"""

from datetime import datetime

from pydantic import BaseModel

TOPIC_TASK_REQUESTED = "agent.task.requested"
TOPIC_TASK_RESUMED = "agent.task.resumed"
TOPIC_TASK_COMPLETED = "agent.task.completed"
TOPIC_TASK_FAILED = "agent.task.failed"


class AgentTaskRequested(BaseModel):
    """Published by the Gateway when a user submits a new goal."""

    event_type: str = TOPIC_TASK_REQUESTED
    version: str = "1.0"
    task_id: str
    owner: str
    goal: str
    timestamp: datetime


class AgentTaskResumed(BaseModel):
    """Published by the Gateway after a human approves/rejects a parked tool call.

    Any worker consumes this, loads the checkpoint (task row + step log), and
    continues from where the task was parked.
    """

    event_type: str = TOPIC_TASK_RESUMED
    version: str = "1.0"
    task_id: str
    approval_id: str
    step_idx: int
    decision: str  # "approved" | "rejected"
    timestamp: datetime


class AgentTaskCompleted(BaseModel):
    """Published by a worker when a task reaches a successful terminal state."""

    event_type: str = TOPIC_TASK_COMPLETED
    version: str = "1.0"
    task_id: str
    timestamp: datetime


class AgentTaskFailed(BaseModel):
    """Published by a worker when a task fails terminally."""

    event_type: str = TOPIC_TASK_FAILED
    version: str = "1.0"
    task_id: str
    error: str
    timestamp: datetime
