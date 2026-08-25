---
name: jarvis-agent
description: Use when working on the JARVIS agent orchestration layer — the reason/act loop, task planning, tool selection, multi-step tasks, iteration limits, context assembly, tool-result handling, and error recovery. Triggers include "agent loop", "planner", "orchestrator", "multi-step task", "tool-calling loop", "agent doesn't finish". Load with jarvis-core; pair with jarvis-llm and jarvis-tools.
---

# JARVIS Agent

The agent orchestrates a user request into a final response by combining LLM reasoning with tool execution. It is the only component allowed to drive the LLM ↔ tool cycle. See jarvis-core for the full architecture.

## Agent loop

```text
Request → Context → Plan → LLM → Tool call → Validate → Permission → Execute → Result → LLM → …repeat… → Completion
```

Each turn: assemble context, call the LLM with the registered tool schemas, and if the model requests tools, run them and feed results back. Continue until the model returns a final answer (no tool calls) or the iteration cap is hit.

## Hard rules

- **Iteration cap.** Enforce `max_tool_iterations` (e.g. 6–8). If exceeded, stop and return a clear message — never loop forever. See jarvis-security (loop prevention).
- **Never skip the pipeline.** Every tool call goes through argument validation → permission check → execution → structured result. The agent must not call utilities or the OS directly. See jarvis-tools and jarvis-security.
- **Feed results back honestly.** Append real tool outputs (success or error) to the conversation; never fabricate a tool result.

## Tool calling

Use the provider's tool interface via jarvis-llm. Support the **hybrid** approach: native OpenAI-style tool calls when the provider supports them, and a JSON-prompt fallback when it does not (`provider.supports_native_tools == False`). The agent normalizes both into the same execute-and-append flow.

## Multi-step tasks

The agent must sequence steps. Example — "Create a project folder, add `main.py`, write starter code, open it in VS Code":

```text
create_folder → create_file → write_file → open_application → report completion
```

Plan the ordered steps, execute each through the tool pipeline, carry forward results, and only report completion once every step has actually succeeded.

## Context & memory

Keep short-term context (the running conversation) bounded — trim or summarize old turns to respect the model's context window and the 8 GB machine. Pull only *relevant* long-term context from memory; never dump the whole store. See jarvis-memory.

## Error recovery

Catch tool and provider errors, surface them to the LLM so it can adapt or ask the user for clarification, and return a friendly message. Retry transient failures with backoff where sensible (see jarvis-llm). A failing tool must not crash the agent.

## Tasks

Long-running work is tracked by the task engine (`app/tasks/`) with statuses: PENDING, PLANNING, RUNNING, WAITING_FOR_CONFIRMATION, COMPLETED, FAILED, CANCELLED. Surface active tasks to the GUI (jarvis-gui).

## Definition of done

Requested steps executed end-to-end, iteration cap respected, every action validated and permissioned, errors handled gracefully, and the agent reports true completion — not pseudocode or a stopping point.
