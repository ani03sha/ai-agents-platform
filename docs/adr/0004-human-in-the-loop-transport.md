# ADR-0004: SSE-Down / POST-Up for Streaming and Human Approvals

## Context

The platform has two distinct communication needs around a running task:

1. **Server → client:** stream the agent's live reasoning (each ReAct step) and surface pending approval
   requests, in real time, to a UI or CLI.
2. **Client → server:** deliver a human's approve/reject decision for a high-stakes tool call.

The directions are asymmetric: reasoning is a high-frequency one-way push; approvals are infrequent
discrete commands. We also require statelessness and compatibility with the existing Traefik gateway, and
we want to reuse the SSE pattern already built in the RAG query service.

A separate but related requirement: the approval gate must be enforced by the *system*, not by trusting the
LLM to "ask first."

## Decision

**Use Server-Sent Events for the downstream stream and ordinary POST endpoints for upstream decisions.**

### Downstream: SSE

`GET /v1/tasks/{id}/stream`:
1. On connect, **replay** existing steps from Postgres `task_steps` (catch-up for late joiners /
   reconnects).
2. Then **live-tail** the Redis pub/sub channel `task:{id}:steps`, to which the worker publishes each step
   (and each approval request) as it happens.
3. Emit SSE events to the client.

Steps are durably written to Postgres regardless of whether anyone is streaming; Redis is only the
ephemeral fan-out.

### Upstream: POST

- `POST /v1/tasks/{id}/approve` `{approval_id}`
- `POST /v1/tasks/{id}/reject`  `{approval_id, reason?}`

The Gateway records the decision on the `approvals` row and publishes `agent.task.resumed` (ADR-0002). A
rejection is fed back to the agent as an observation, prompting it to re-plan — it is not a task failure.

### Enforcement

A `requires_approval` tool (ADR-0003) **cannot execute** without an `APPROVED` decision recorded for that
exact `(task_id, step_idx)`. The worker parks the task at the gate and only resumes the tool call after
consuming a resume event tied to the approval. Approval is a property of the execution model, not a prompt
instruction.

## Consequences

**Positive**
- Stateless and Traefik-friendly: SSE is plain HTTP; POSTs are ordinary requests. Any Gateway instance
  serves any client; any worker handles any resume.
- Reuses the RAG SSE implementation; only the Postgres catch-up replay is new.
- Clean separation: high-frequency push (SSE) vs infrequent commands (POST) use the right tool for each.
- Late joiners and reconnects get the full reasoning trace via replay, then continue live.

**Negative / costs**
- Two channels instead of one (vs a single WebSocket). Acceptable given the asymmetric traffic.
- SSE is one-directional by definition, so approvals need a separate endpoint, which we wanted anyway for
  auditable, idempotent commands.

## Alternatives considered

1. **WebSocket (single bidirectional channel)**: carries reasoning down and approvals up over one socket.
   Richer, but a stateful long-lived connection: harder to route through Traefik and to scale across
   stateless Gateway instances, and overkill for infrequent approvals. *Rejected.*
2. **Polling `GET /tasks/{id}`**: trivially stateless, but high latency and wasteful for live reasoning.
   *Rejected* as the primary stream; remains available as a fallback for status.
3. **Trusting the LLM to request approval in-band** (no enforced gate): unsafe; the model can ignore the
   instruction. *Rejected* — approval must be structurally enforced.
