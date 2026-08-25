---
name: jarvis-debugging
description: Use when diagnosing and fixing bugs or crashes in JARVIS. Enforces a disciplined reproduce → inspect logs → root-cause → minimal fix → targeted test → full-suite → verify workflow, and forbids rewriting large working sections to fix a small bug. Triggers include "fix crash", "bug", "error", "traceback", "not working", "debug", "regression". Load with jarvis-core; pair with jarvis-testing.
---

# JARVIS Debugging

Fix bugs surgically while preserving working functionality. See jarvis-core (development behavior).

## Workflow

```text
Reproduce → Inspect logs → Identify root cause → Minimal fix → Targeted test → Full tests → Verify application
```

1. **Reproduce** the issue before changing anything.
2. **Inspect logs** first — JARVIS logs tool selections, executions, permission decisions, task status, LLM latency, and errors (without secrets — jarvis-security). The answer is often already there.
3. **Find the root cause**, not just the symptom.
4. **Make the minimal fix.** Do not mass-rewrite modules or refactor unrelated code to patch one bug.
5. **Add a targeted regression test** (jarvis-testing), then run the **full suite**.
6. **Verify** the app still works end-to-end.

## Preserve working functionality

Never delete or rewrite large sections that already work in order to fix something small. Keep the architecture intact (jarvis-core) — don't bypass the agent/tool/permission pipeline to force a fix.

## Don't patch-loop

If an approach fails twice, stop and diagnose the real cause instead of making more incremental tweaks. Explain what's actually wrong, then apply a correct fix. If the correct fix would change agreed scope or architecture, flag it first.

## Definition of done

Root cause identified, minimal fix applied, a regression test added, the full suite passes, existing functionality preserved, and the app verified.
