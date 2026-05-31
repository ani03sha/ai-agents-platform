# ADR-0001: Build the Agent Core From Scratch (No Agent Framework)

## Context

LLM agent frameworks exist like LangChain (agents), AutoGen, CrewAI, LlamaIndex agents. Each provides a
ready-made ReAct loop, tool abstraction, planner, and multi-agent orchestration. Using one would get a demo
running in an afternoon.

The goal of this project is the opposite of a fast demo. It is to build a *reference-grade* understanding
of how agents actually work, suitable for principal-level scrutiny and a blog series titled "A First
Principles Approach." The same philosophy governed the predecessor distributed RAG system, where retrieval,
ranking, and caching were built directly rather than delegated to a framework.

There is also a real engineering cost to frameworks: they move the core control flow (the loop, the parse
step, the prompt format, the termination logic) behind abstractions that change between minor versions,
hide the exact prompt sent to the model, and make failure modes hard to diagnose.

## Decision

**Implement the agent core from scratch**: the ReAct loop, the output parser, the prompt builder, the tool
registry and dispatch, the planner, the critic, and the multi-agent orchestrator. No LangChain agents, no
AutoGen, no CrewAI in the domain layer.

To preserve optionality, the core is built behind `Protocol` ports (`LLMProvider`, `Tool`, `ToolRegistry`,
`TaskStore`, `AgentMemory`, etc.). A framework can later be introduced as an **adapter** behind one of these
ports; for example, a `LangChainToolRegistry` without touching the domain.

## Consequences

**Positive**

- Complete visibility into the exact prompt, the parse logic, and every loop decision. This is the entire
  point.
- No version-churn risk in the core; the ReAct pattern long outlives any library.
- Failure modes (malformed output, tool errors, runaway loops) are handled by code we wrote and understand.
- Frameworks remain available later as adapters, for benchmarking ("our loop vs LangChain's").

**Negative / costs**

- More code to write and maintain than `pip install` + 20 lines.
- We re-derive solutions to problems frameworks already solved (output parsing robustness, context-window
  management). We accept this as the cost of understanding.
- We must build our own evaluation and observability rather than inherit a framework's.

**Mitigations**

- Keep the from-scratch surface small and well-tested: a parser, a loop, a registry, four agent roles.
- Lean on the hexagonal boundary so the "hard" infra (Postgres, Qdrant, Redpanda) is reused from the RAG
  project, not reinvented.

## Alternatives considered

1. **LangChain/LlamaIndex agents:** fastest start, but hides the loop and the prompt, churns across
   versions, and defeats the learning goal. *Rejected* as the core; allowed later as an adapter.
2. **AutoGen / CrewAI multi-agent:** strong multi-agent ergonomics, but opinionated orchestration we want
   to design ourselves. *Rejected* as the core.
3. **Thin wrapper over a framework:** still inherits the framework's control flow and opacity. *Rejected.*