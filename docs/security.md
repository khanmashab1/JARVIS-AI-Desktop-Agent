# JARVIS Security & Permission Model

Security is the highest-priority concern in JARVIS. Python executes actions; the LLM is restricted from directly touching operating system APIs or issuing arbitrary shell commands.

## 1. Risk Level Classification

Every tool carries a risk rating:
- **`SAFE`**: Read-only queries, telemetry, time, system status, web search. Auto-approved.
- **`LOW`**: File creation, appending, note storage, project scaffolding. Auto-approved by default.
- **`MEDIUM`**: Moving files, closing applications, running test suites. Audited; optional confirmation.
- **`HIGH`**: File deletion, destructive modifications. **Requires human confirmation modal**.
- **`CRITICAL`**: Shell execution, elevated operations. **Requires explicit human approval**.

## 2. Confirmation UI Modal

When a tool requires approval:
1. The agent pauses execution.
2. A modal dialog is presented to the user displaying:
   - Tool name
   - Risk level
   - Target parameters (e.g. file path or command)
   - [Approve] and [Reject] buttons.
3. If approved, the tool executes and results are returned to the agent loop.
4. If rejected, a denial result is fed back to the LLM so it can inform the user gracefully.

## 3. Path Traversal & Filesystem Restrictions

- `InputSanitizer` resolves and checks every file target against configured `allowed_filesystem_roots`.
- Traversal attempts (`../`, unapproved drive roots) raise a `SecurityViolationError` immediately before any file system call is made.

## 4. Credential Protection & Redaction

- API keys and tokens are loaded strictly from the environment or masked `.env`.
- `.env` is ignored by Git in `.gitignore`.
- Python logging uses a `RedactingFormatter` that scrubs authorization headers, bearer tokens, and API keys matching `sk-...`, `tabi-...`, and regex secret patterns.
