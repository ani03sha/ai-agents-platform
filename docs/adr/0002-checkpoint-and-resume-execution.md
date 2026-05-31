# ADR-0002: Event-Driven, Checkpoint-and-Resume Execution Model

## Context

An agent task is fundamentally long-running and may pause for an unbounded time:

- A multi-step ReAct loop against a local 14B model takes seconds-to-minutes per step.
- A human-in-the-loop approval (ADR-0004) can leave a task idle for minutes or hours.
- The platform must scale horizontally and survive worker crashes (a core design principle inherited from
  the RAG system: stateless services, state in the data layer).

We need an execution model that handles indefinite pauses, horizontal scale, and crash recovery without
losing work.

## Decision

**Execute tasks asynchronously through Redpanda, and model agent state as an append-only step log in
PostgreSQL. The step log is the checkpoint.**

Specifics:

1. The Gateway publishes `agent.task.requested` and returns a `task_id` immediately. Workers consume and
   execute.
2. After **every** ReAct step, the worker appends one immutable row to `task_steps`
   `(task_id, idx, agent_role, thought, action_tool, action_input, observation)`. The complete, resumable
   state of a task is `task row + ordered task_steps`; no opaque object serialization.
3. On a `requires_approval` tool, the worker writes a pending `approval`, sets status
   `AWAITING_APPROVAL`, **commits the Kafka offset, and returns**; freeing the consumer slot. The task is
   *parked*, not held in memory.
4. A human decision causes the Gateway to publish `agent.task.resumed`. **Any** worker consumes it, loads
   the checkpoint, and continues from where the parked task left off.
5. At-least-once delivery is made idempotent by the `UNIQUE (task_id, idx)` constraint plus a check for
   whether a step already has an observation before (re)executing its tool.

## Consequences

**Positive**
- **Crash-safety is free.** "Resume after a pause" and "recover after a crash" are the same code path:
  load the step log, continue. A worker can die at any point; another resumes.
- **Indefinite pauses cost nothing.** A parked task holds no worker slot, no memory, no connection.
- **True statelessness.** No worker affinity; any instance handles any task. Scales horizontally.
- **Auditability and explainability.** The step log is a complete, replayable record of the agent's
  reasoning — also the data source for SSE catch-up and for evaluation.
- **No serialization/versioning hazard.** We never pickle an agent; we replay structured rows.

**Negative / costs**
- A DB write per step adds latency and load (acceptable: steps are seconds apart, dominated by LLM time).
- Reconstructing the prompt scratchpad from the log each resume costs a read; for very long tasks we add a
  rolling summary of older steps to bound context.
- More moving parts than an in-process loop (Redpanda + Postgres + idempotency logic).

## Alternatives considered

1. **Synchronous execution inside the HTTP request:** simplest, but breaks on timeouts, client
   disconnects, and offers no horizontal scaling or HITL pauses. *Rejected.*
2. **In-worker blocking on approval:** keep agent state in memory and block waiting for the human. A
   worker crash loses all progress, and long human delays pin a consumer slot. *Rejected* (weaker
   production story; this was the explicit fork at design time).
3. **Opaque state serialization (pickle the agent):** resumable but brittle across code changes and
   opaque to auditing/eval. *Rejected* in favor of the structured step log.
4. **A durable-execution engine (Temporal):** solves long-running/retry/replay industrially, and is a
   reasonable *future adapter* behind the execution port. *Deferred*: building the model ourselves is the
   learning goal (see ADR-0001); Temporal can replace the hand-rolled layer later without domain changes.

## Notes

This decision is the spine of the platform. Multi-agent coordination (Planner/Executor/Critic) runs as more
steps in the *same* log, so pause/resume/crash-safety apply uniformly to single- and multi-agent runs.
