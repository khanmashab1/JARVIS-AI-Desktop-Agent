---
name: jarvis-tools
description: Use when creating, modifying, or registering JARVIS tools — the only way the agent is allowed to act on the system. Covers the Tool contract, the central ToolRegistry, parameter schemas and validation, risk levels, and tool categories (applications, filesystem, system, browser, vision, productivity, development). Triggers include "add a tool", "tool registry", "open_application", "create_file", "register capability". Load with jarvis-core and jarvis-security.
---

# JARVIS Tools

Tools are discrete, validated, permissioned capabilities. They are the *only* bridge between the LLM's decisions and the real machine. The agent must never reach the OS directly — it goes through a registered tool. See jarvis-core.

## Tool contract

Every tool defines:

```text
name                 unique identifier the LLM references
description          clear, action-oriented; drives correct selection
parameters           JSON schema (types + required)
risk_level           SAFE | LOW | MEDIUM | HIGH | CRITICAL
requires_confirmation derived from risk (see below)
execute(**kwargs)    performs the action, returns a structured ToolResult
```

`execute()` returns a structured result (success flag, output, error) — never a bare string or an unhandled exception. Catch failures and return them as an error result.

## Central registry

Register every tool in the `ToolRegistry`. The agent discovers and calls tools only through it, and the registry produces the tool schemas passed to the LLM. Do **not** add ad-hoc utility calls from the agent or from plugins — plugins register through the same registry (see jarvis-plugins).

## Categories

Applications, Filesystem, System, Browser, Vision, Productivity, Development.

## Risk levels

```text
SAFE      get_current_time, open_application, get_system_information
LOW       create_file, create_folder, write_note
MEDIUM    move_file, copy_file, browser navigation to new domains
HIGH      delete_file, bulk file operations
CRITICAL  anything resembling arbitrary shell/command execution
```

`requires_confirmation` is true for **HIGH** and **CRITICAL**. Those actions must be confirmed by the user before running — enforced by jarvis-security's permission engine, not by ad-hoc `if` checks.

## Validation (mandatory)

Validate arguments against the schema before executing: required fields present, correct types, reject/ignore unknown fields. Sanitize inputs to prevent injection and path traversal. For process launches use list-form `subprocess` (never `shell=True`) and an allowlist of known apps. For filesystem tools, confine paths to configured allowed roots. See jarvis-security.

## No open-ended shell

Do not implement a general `execute_shell_command` tool with unrestricted input. If a CRITICAL capability is ever truly needed, it must be narrowly scoped, explicitly designed, risk-classed CRITICAL, and gated behind confirmation.

## Cross-platform

Target Windows first, but implement tools to also work on macOS/Linux (platform dispatch) so behavior is portable and testable.

## Definition of done

Tool is registered, schema-validated, risk-classified, returns structured results, handles its own errors, and has tests (see jarvis-testing) — including a permission test for MEDIUM+ tools.
