---
name: jarvis-browser
description: Use when implementing JARVIS browser automation with Playwright — controlled navigation and read operations such as open_url, search_web, browser_back, browser_forward, refresh_page, get_page_title, and get_page_text. Sensitive actions (logins, purchases, messages, form submissions) require explicit confirmation. Triggers include "browser", "Playwright", "open URL", "web search", "navigate", "scrape page", "automate the browser". Load with jarvis-core, jarvis-tools, and jarvis-security.
---

# JARVIS Browser

Browser automation uses **Playwright** and is exposed to the agent as tools registered in the ToolRegistry (see jarvis-tools) — the agent never drives the browser directly.

## Controlled operations

```text
open_url | search_web | browser_back | browser_forward | refresh_page | get_page_title | get_page_text
```

These are the sanctioned building blocks. Add new browser actions as registered, risk-classed tools.

## Risk & confirmation

Reads and simple navigation are LOW/MEDIUM risk. **Sensitive actions require explicit user confirmation** (jarvis-security): never automatically log in, purchase, send messages, delete content, or submit forms containing sensitive data. Prompt the user first, stating what will happen.

## Credentials

Never auto-fill or submit credentials. Do not store passwords in code or logs. If a site requires login, hand control to the user or require confirmation.

## Lifecycle & resilience

Manage the browser/context lifecycle explicitly; reuse a context where sensible and close it to free resources (jarvis-performance). Handle a closed browser, navigation timeouts, and missing elements gracefully — return a structured tool error, never crash JARVIS.

## Concurrency

Run Playwright operations off the GUI thread (jarvis-gui). Apply timeouts to every navigation/action (jarvis-security).

## Definition of done

Operations exposed as registered tools with risk levels, sensitive actions gated behind confirmation, no automatic credential handling, robust error/timeout handling, and tests using a mocked browser (see jarvis-testing).
