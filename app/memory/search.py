"""Search and selective retrieval for memory items."""

import re
from typing import List, Optional
from app.memory.models import MemoryItem


def _tokenize(text: str) -> set[str]:
    """Simple lowercase alphanumeric tokenization."""
    return set(re.findall(r"\w+", text.lower()))


class MemorySearcher:
    """Calculates relevance scores to select only relevant memories for context."""

    @staticmethod
    def search(
        memories: List[MemoryItem],
        query: str,
        limit: int = 5,
        min_score: float = 0.1,
    ) -> List[MemoryItem]:
        """Rank memories by token overlap and keyword matches."""
        if not query.strip() or not memories:
            return []

        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored_items: List[tuple[float, MemoryItem]] = []

        for item in memories:
            combined_text = f"{item.key} {item.content} {item.memory_type}"
            item_tokens = _tokenize(combined_text)
            if not item_tokens:
                continue

            # Jaccard / Overlap similarity
            intersection = query_tokens.intersection(item_tokens)
            if not intersection:
                # Substring check for project names or exact phrases
                if query.lower() in combined_text.lower() or item.key.lower() in query.lower():
                    scored_items.append((0.5, item))
                continue

            score = len(intersection) / len(query_tokens)
            # Boost if query contains exact key
            if item.key.lower() in query.lower():
                score += 0.5

            if score >= min_score:
                scored_items.append((score, item))

        scored_items.sort(key=lambda x: x[0], reverse=True)
        return [item for score, item in scored_items[:limit]]
