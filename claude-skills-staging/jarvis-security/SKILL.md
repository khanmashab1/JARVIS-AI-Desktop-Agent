---
name: jarvis-security
description: Highest-priority skill governing every security-sensitive decision in JARVIS. Use whenever work touches secrets, API keys, permissions, tool risk, confirmations, filesystem/network restrictions, input validation, timeouts, loop limits, auditing, or privacy (local vs remote, camera/mic indicators). Any skill that performs actions defers to this one. Triggers include "permission", "confirmation", "secret", "API key", "dangerous operation", "validate input", "sandbox". Load with jarvis-core.
---

# JARVIS Security

Security overrides all other skills. If any feature skill conflicts with this one, this one wins (see the cross-skill priority in jarvis-core).

## Secrets

Never hard-code secrets. Load API keys, tokens, and base URLs from environment/`.env`, and keep `.env` out of source control (`.gitignore`). Never log keys, tokens, or passwords — redact them in logs. Never expose credentials to the LLM unless explicitly required and user-approved.

## Permission engine

Tools carry a risk level (SAFE, LOW, MEDIUM, HIGH, CRITICAL — see jarvis-tools). The permission engine, not scattered `if` statements, decides what needs approval:

- SAFE / LOW: run directly.
- MEDIUM: run, but audit; confirm when configured.
- HIGH / CRITICAL: **require explicit user confirmation** before executing.

Confirmation prompts state what will happen, why, how many items are affected, and whether it is reversible, e.g.:

```text
JARVIS wants to: Delete 14 files.   [Approve] [Reject]
```

## Input validation & sandboxing

Validate every tool parameter against its schema. Sanitize inputs to prevent command injection (list-form subprocess, never `shell=True`) and path traversal. Restrict filesystem access to configured allowed roots. The LLM never receives raw shell, filesystem, or network access — only registered tools.

## Robustness limits

Apply timeouts to all external calls (LLM, browser, network). Enforce the agent's iteration cap to prevent infinite loops (see jarvis-agent). A failing component must degrade gracefully, not crash JARVIS.

## Auditing

Log important actions — tool name, risk level, permission decision, task id — without sensitive data. This supports review and debugging (see jarvis-debugging) while honoring the "never log secrets" rule.

## Privacy

Clearly distinguish LOCAL processing from REMOTE API calls. The app must indicate when data is sent to a remote provider and when the camera or microphone is active (see jarvis-gui, jarvis-vision, jarvis-voice). Prefer local components for sensitive input where practical.

## Ethical boundaries

Do not implement hidden surveillance, credential theft, spyware, or unauthorized access. Security-testing capabilities are limited to systems the user owns or is explicitly authorized to test. Camera/mic features are always opt-in and visible.

## Definition of done

Secrets are external and unlogged, inputs validated, risky actions permissioned and confirmed, external calls timed out, loops bounded, important actions audited, and privacy indicators present.
