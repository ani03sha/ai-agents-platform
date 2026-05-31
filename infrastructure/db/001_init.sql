-- 001_init.sql — initial schema for the AI Agents Platform.
-- Idempotent (safe to re-run). task_steps IS the checkpoint (ADR-0002).

CREATE TABLE IF NOT EXISTS api_keys(
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash TEXT NOT NULL,
    owner TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    revoked_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS tasks(
    id UUID PRIMARY KEY,
    owner TEXT NOT NULL,
    goal TEXT NOT NULL,
    status TEXT NOT NULL, -- TaskStatus (app-enforced)
    plan JSONB, -- [{idx, role, subtask}]
    result TEXT,
    current_step INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_task_owner ON tasks(owner);
CREATE INDEX IF NOT EXISTS idx_task_status ON tasks(status);

-- The append-only step log == the checkpoint == short-term memory.
CREATE TABLE IF NOT EXISTS task_steps(
    id BIGSERIAL PRIMARY KEY,
    task_id UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    idx INT NOT NULL, -- monotonic per task
    agent_role TEXT NOT NULL, -- planner | research | code | writing | critic
    thought TEXT,
    action_tool TEXT,  -- null on a Final answer step
    action_input JSONB,
    observation TEXT, -- tool result or final answer
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(task_id, idx) -- makes at-least one replay idempotent
);
CREATE INDEX IF NOT EXISTS idx_task_steps_task ON task_steps (task_id, idx);

CREATE TABLE IF NOT EXISTS approvals (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    task_id     UUID NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    step_idx    INT  NOT NULL,
    tool        TEXT NOT NULL,
    tool_input  JSONB NOT NULL,
    reason      TEXT NOT NULL,               -- the agent's stated justification
    status      TEXT NOT NULL DEFAULT 'PENDING',  -- PENDING|APPROVED|REJECTED
    decided_by  TEXT,
    decided_at  TIMESTAMPTZ,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_approvals_task ON approvals (task_id, status);

CREATE TABLE IF NOT EXISTS audit_log(
    id BIGSERIAL PRIMARY KEY,
    task_id UUID,
    actor TEXT NOT NULL,
    detail JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audit_task ON audit_log (task_id);