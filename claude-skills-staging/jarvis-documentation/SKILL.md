---
name: jarvis-documentation
description: Use when creating or updating JARVIS documentation — README, architecture, installation, configuration, API/provider setup, tools, plugins, security, voice, vision, and troubleshooting. Enforces keeping docs synchronized with the actual implementation so nothing describes features that no longer exist. Triggers include "update docs", "README", "document this", "docs out of date", "write documentation". Load with jarvis-core.
---

# JARVIS Documentation

Documentation must always match the real implementation. Out-of-date docs are worse than none.

## What to document

Architecture, installation, configuration, API/LLM provider setup, available tools, plugins, security model, voice, vision, and troubleshooting.

## The synchronization rule

Update docs **in the same change** as the code they describe. Never leave documentation describing removed or nonexistent functionality. When a feature is added, changed, or deleted, update the relevant docs immediately.

## README structure

Keep the project README aligned with the spec: overview, features, architecture, installation, configuration, API setup, running JARVIS, available tools, security model, screenshots, development roadmap, and troubleshooting.

## Configuration & dependencies

Document all environment variables (`LLM_PROVIDER`, `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, feature flags) and every major dependency and why it's needed (see jarvis-core: dependency rules). Never put real secrets in docs — use placeholders and reference `.env.example`.

## Style

Concise, accurate, example-driven. Prefer prose and small code/config examples over walls of text. Reflect the actual module layout and tool names so readers can navigate the code.

## Definition of done

Docs reflect current behavior, no stale/phantom features remain, env vars and major deps are documented with placeholders (no secrets), and the README structure is intact.
