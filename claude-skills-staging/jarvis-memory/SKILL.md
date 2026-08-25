---
name: jarvis-memory
description: Use when implementing or changing JARVIS memory — short-term conversation context and long-term SQLite-backed storage of preferences, facts, projects, tasks, and notes. Covers save/search/delete, selective retrieval, the MemoryManager structure, and privacy. Triggers include "remember that", "recall", "memory", "conversation history", "store preference", "SQLite", "forget". Load with jarvis-core; pair with jarvis-agent and jarvis-security.
---

# JARVIS Memory

JARVIS has short-term memory (the current conversation) and long-term memory (persistent across sessions). Memory feeds the agent's context but is deliberately *selective*. See jarvis-core.

## Storage

SQLite initially. Design the layer so a vector/semantic store can be added later without changing callers — keep persistence behind a repository interface.

## Structure

```text
MemoryManager
 ├── ConversationMemory   short-term running context
 ├── UserMemory           preferences, facts
 ├── TaskMemory           tasks, prior work
 └── SemanticMemory       future embeddings/vector search
```

## Categories

```text
conversation | preference | fact | project | task | note
```

## Core operations

```text
save_memory(category, content, metadata)
search_memory(query, category?, limit?)
delete_memory(id | query)
```

## Selective retrieval — critical

**Never send the entire database to the LLM.** Retrieve only relevant context by category, recency, and keyword (later: embeddings). This keeps prompts small and fast on the 8 GB target machine (see jarvis-performance) and respects privacy.

## Privacy & consent

Do not silently store sensitive information. Long-term storage of personal facts should be user-approved (e.g. explicit "remember that…"). Never persist secrets/credentials. Redaction and privacy rules follow jarvis-security. Support deletion so users can remove stored items.

## Definition of done

Persistence behind an interface, categories enforced, retrieval is scoped (not whole-DB), sensitive data is not silently stored, deletion works, and operations are covered by tests with a temporary database (see jarvis-testing).
