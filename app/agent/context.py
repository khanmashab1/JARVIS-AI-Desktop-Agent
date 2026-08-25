"""Context builder assembling messages, selective memories, and prompt budgets."""

from typing import Any, Dict, List, Optional
from app.agent.prompts import get_system_prompt
from app.memory.manager import MemoryManager
from app.utils.logging import get_logger

logger = get_logger("agent.context")


class ContextBuilder:
    """Constructs prompt messages for LLM completions."""

    def __init__(self, memory_manager: Optional[MemoryManager] = None, max_history_turns: int = 10) -> None:
        self.memory = memory_manager
        self.max_history_turns = max_history_turns

    def build_context(
        self,
        user_input: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        active_task_context: Optional[str] = None,
        custom_instructions: str = "",
    ) -> List[Dict[str, Any]]:
        """Construct full message payload with system prompt, memory snippets, and recent turns."""
        messages: List[Dict[str, Any]] = []

        # 1. System Prompt
        sys_prompt = get_system_prompt(custom_instructions)

        # 2. Selective Long-term Memory Injection
        if self.memory and user_input:
            relevant = self.memory.get_relevant_memories(user_input, limit=4)
            if relevant:
                memory_snippets = []
                for m in relevant:
                    memory_snippets.append(f"- [{m.memory_type.upper()}] {m.key}: {m.content}")
                sys_prompt += "\n\nRelevant Stored Information About User / Projects:\n" + "\n".join(memory_snippets)

        if active_task_context:
            sys_prompt += f"\n\nCurrently Active Multi-Step Task Context:\n{active_task_context}"

        messages.append({"role": "system", "content": sys_prompt})

        # 3. Conversation History (sliding window)
        if conversation_history:
            # Keep only the last N turns (user + assistant)
            recent = conversation_history[-(self.max_history_turns * 2):]
            messages.extend(recent)

        # 4. Current User Message (if not already the last item in history)
        if not conversation_history or (conversation_history and conversation_history[-1].get("content") != user_input):
            messages.append({"role": "user", "content": user_input})

        return messages
