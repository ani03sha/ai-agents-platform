# ADR-0003: Schema-First Tool Registry; Defer Code Execution

## Context

Tools are the interface between the agent and the world. The LLM decides *whether* and *how* to call a tool
based entirely on the text we give it: the tool's name, description, and parameter schema. A vague
description or a loose parameter spec is the single largest cause of incorrect tool calls.

Two questions must be settled:

1. **How are tools defined and dispatched** so the loop stays decoupled from any specific tool?
2. **Which tools ship first**, given that the originally proposed `code_execute` (run LLM-generated code via
   `subprocess` + timeout) is *not a security boundary* - generated code could read the filesystem,
   environment variables, and network.

## Decision

### Schema-first tool registry

Every tool implements a `Tool` `Protocol`:

```python
class Tool(Protocol):
    name: str                # stable id the LLM emits in `Action:`
    description: str         # WHAT it does + WHEN to use it — treated as prompt text
    parameters_schema: dict  # JSON Schema; validated before run()
    requires_approval: bool  # high-stakes → HITL gate (ADR-0004)
    async def run(self, args: dict) -> ToolResult: ...
```

A `ToolRegistry` (a) holds the subset of tools available to each agent role, (b) renders `list_schemas()`
into the system prompt, (c) **validates `action_input` against `parameters_schema` before dispatch**, and
(d) routes to `run()`. Validation failures and tool exceptions are returned to the agent as *observations*,
never raised as crashes — the agent gets a chance to correct itself.

Tool descriptions are owned and reviewed as prompt artifacts, not afterthoughts.

### Initial tool set

| Tool             | requires_approval | Notes                                          |
|------------------|-------------------|------------------------------------------------|
| `web_search`     | no                | Current information                            |
| `rag_retrieve`   | no                | Calls the distributed RAG system as a tool     |
| `calculator`     | no                | Safe arithmetic expression evaluation          |
| `http_request`   | **yes**           | Outbound call to a whitelisted host; gated     |
| `memory_write`   | no                | Persist a fact to long-term memory (Qdrant)    |
| `memory_recall`  | no                | Semantic search of long-term memory            |

### Defer code execution

**No `code_execute` tool in the initial system.** The above tool set is sufficient to demonstrate the full
ReAct loop, multi-agent coordination, memory, and HITL. A sandboxed code-execution tool is a planned later
component with its own design and blog post, and will require a real isolation boundary (an ephemeral
locked-down container: no network, CPU/memory/time caps, read-only FS) — added as a new adapter behind the
same `Tool` port, with **zero changes to the loop**.

## Consequences

**Positive**
- Adding/removing a tool is a one-class change; the loop never changes.
- Pre-dispatch schema validation turns a class of "wrong arguments" failures into self-correcting
  observations.
- Per-role tool subsets keep prompts small and reduce tool confusion.
- Deferring code execution avoids shipping a fake security boundary; the "production-grade" claim stays
  honest.

**Negative / costs**
- Writing good tool descriptions and schemas is real prompt-engineering work, done per tool.
- Until the sandbox lands, the platform cannot run arbitrary computation; `calculator` + `http_request`
  cover the common cases for now.

## Alternatives considered

1. **`subprocess` + timeout for code execution** (original proposal): simple, but not isolation: stops
   runaway loops, not FS/env/network access. *Rejected* for the initial system; will be replaced by a
   container sandbox when code execution is added.
2. **Native model tool-calling format (OpenAI-style function calling)**: convenient where supported, but
   couples us to a provider's API and hides the format we want to teach. *Rejected* for the core; the ReAct
   text format is provider-agnostic and explicit. A function-calling adapter remains possible later.
3. **One mega-agent with all tools**: simpler wiring, but prompt bloat and tool confusion. *Rejected* in
   favor of per-role registries (see multi-agent design).
