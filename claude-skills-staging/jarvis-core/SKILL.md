---
name: jarvis-core
description: Foundational skill for the JARVIS AI Desktop Agent (a modular Python app where an LLM reasons and Python executes). Load this FIRST for any JARVIS work — it defines the overall architecture, module layout, project principles, target hardware, coding standards, development behavior, cross-skill priority, and how to add a new capability. Pair it with the relevant feature skill (jarvis-agent, jarvis-llm, jarvis-tools, jarvis-voice, jarvis-gui, etc.).
---

# JARVIS Core

JARVIS is a **modular AI Desktop Agent** built in Python. The **LLM is the reasoning layer**; **Python is the execution layer**. The LLM decides *what* to do; it never touches the machine directly — every action goes through the tool + permission system.

It combines: LLM reasoning, tool calling, voice, desktop automation, browser automation, memory, vision, GUI, task management, plugins, security, and system monitoring.

## Canonical architecture — never bypass this

```text
User
 ↓
Interface  (GUI  |  Voice)
 ↓
Agent  (orchestration loop)
 ↓
Context  →  Memory
 ↓
LLM  (reasoning + tool selection)
 ↓
Tool Selection
 ↓
Permission Engine
 ↓
Tool Execution
 ↓
Result  →  Agent  →  Response
```

Adding a new capability always follows: **Tool → Registry → Permission → Agent → LLM.** Do not let the LLM, GUI, voice, browser, or a plugin reach the system except through a registered, permission-checked tool.

## Module layout (`app/`)

```text
app/agent/      orchestration, planning, prompts     → jarvis-agent
app/providers/  llm/ stt/ tts/ abstractions          → jarvis-llm, jarvis-voice
app/tools/      registry + tool implementations       → jarvis-tools
app/security/   permissions + policies                → jarvis-security
app/memory/     SQLite + memory manager               → jarvis-memory
app/tasks/      task engine                           → jarvis-agent
app/voice/      listener + speaker                     → jarvis-voice
app/gui/        PySide6 windows/pages                 → jarvis-gui
plugins/        optional loadable capabilities         → jarvis-plugins
```

## Project principles

Modular code, no giant files or god-classes. No duplicated logic. Dependency injection where it clarifies wiring. Interfaces/abstractions for every provider (LLM, STT, TTS, vision). Type hints everywhere. Explicit error handling. Tests for important functionality. GUI operations stay non-blocking. Secrets stay out of source control. **Maintainable beats clever.**

## Coding standards

Python 3.11+, PEP 8, clear naming, small functions and classes, explicit error handling, async where it helps, no unnecessary global state. Prefer the layering interface → implementation → service → repository → controller where appropriate. Avoid one giant class or one giant `main.py`.

## Dependencies

Before adding a package: (1) can the standard library do it? (2) does an existing dependency already cover it? (3) only then add it, pinned, and documented in `requirements.txt`. Do not install unnecessary packages.

## Target hardware — optimize for it

```text
CPU: Intel Core i5-1235U   RAM: 8 GB   GPU: Integrated Intel   OS: Windows
```

Prefer remote LLM APIs for heavy reasoning. Do **not** load large local LLMs. Use lightweight local components for STT, TTS, vision, and monitoring. Avoid needless background processes and polling. See jarvis-performance.

## Cross-skill priority

When guidance conflicts, resolve in this order:

```text
Security  >  Core Architecture  >  Feature Skill  >  Implementation Detail
```

A browser/vision/tool/plugin skill can never bypass jarvis-security or this architecture.

## Skill selection (load core + the relevant ones)

- "Add Spotify support" → jarvis-tools, jarvis-plugins
- "Add voice commands" → jarvis-agent, jarvis-voice
- "Make JARVIS remember things" → jarvis-memory, jarvis-agent
- "Add camera eye detection" → jarvis-vision, jarvis-study, jarvis-security
- "Fix this crash" → jarvis-debugging, jarvis-testing

## Development behavior

Inspect the repo first, read the relevant skills, reuse existing abstractions, then implement. Run tests, fix errors, update docs, verify integration, and continue until the task is actually complete. Do **not** stop at pseudocode, do **not** create placeholder implementations when a real one is possible, do **not** duplicate existing functionality, and do **not** ask the user to "start phase 2" — carry the work through.

## Golden rules

Never hard-code secrets or the LLM provider/model. Never give the LLM raw shell, filesystem, or network access. Never skip validation or the permission engine. Never block the GUI thread.
