"""Central orchestrator connecting UI, Voice, Agent, Memory, and Tools."""

import asyncio
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from app.agent.agent import AgentResponse, JarvisAgent
from app.agent.context import ContextBuilder
from app.config import Config
from app.memory.manager import MemoryManager
from app.providers.llm.base import LLMProvider
from app.providers.tts.base import TTSProvider
from app.security.permissions import PermissionEngine
from app.tasks.manager import TaskManager
from app.tools.registry import ToolRegistry
from app.utils.logging import get_logger

logger = get_logger("agent.orchestrator")

KNOWN_CITIES = {
    "dhamtour": "Dhamtour, Abbottabad", "dhamtaur": "Dhamtour, Abbottabad", "دھمتوڑ": "Dhamtour, Abbottabad",
    "abbottabad": "Abbottabad", "ایبٹ آباد": "Abbottabad",
    "haripur": "Haripur", "ہری پور": "Haripur",
    "lahore": "Lahore", "lahaur": "Lahore", "لاہور": "Lahore",
    "karachi": "Karachi", "کراچی": "Karachi",
    "islamabad": "Islamabad", "اسلام آباد": "Islamabad",
    "rawalpindi": "Rawalpindi", "راولپنڈی": "Rawalpindi",
    "peshawar": "Peshawar", "پشاور": "Peshawar",
    "multan": "Multan", "ملتان": "Multan",
    "faisalabad": "Faisalabad", "فیصل آباد": "Faisalabad",
    "quetta": "Quetta", "کوئٹہ": "Quetta",
    "dubai": "Dubai", "دبئی": "Dubai",
    "london": "London", "لندن": "London",
    "new york": "New York", "ٹورانٹو": "Toronto"
}


class JarvisOrchestrator:
    """Coordinates lifecycle, speech input/output, and reasoning turns."""

    def __init__(
        self,
        config: Config,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry,
        permission_engine: PermissionEngine,
        memory_manager: MemoryManager,
        task_manager: TaskManager,
        tts_provider: Optional[TTSProvider] = None,
    ) -> None:
        self.config = config
        self.llm = llm_provider
        self.registry = tool_registry
        self.permissions = permission_engine
        self.memory = memory_manager
        self.tasks = task_manager
        self.tts = tts_provider

        self.context_builder = ContextBuilder(memory_manager=memory_manager)
        self.agent = JarvisAgent(
            llm_provider=llm_provider,
            tool_registry=tool_registry,
            permission_engine=permission_engine,
            max_iterations=config.llm.max_iterations,
            on_activity=self._on_agent_activity,
        )

        self.active_conversation_id: Optional[str] = None
        self.activity_listeners: List[Callable[[str], None]] = []
        self.response_listeners: List[Callable[[str, AgentResponse], None]] = []

        self._init_session()

    def _init_session(self) -> None:
        conv = self.memory.create_conversation("JARVIS Active Session")
        self.active_conversation_id = conv.id

    def add_activity_listener(self, listener: Callable[[str], None]) -> None:
        self.activity_listeners.append(listener)

    def add_response_listener(self, listener: Callable[[str, AgentResponse], None]) -> None:
        self.response_listeners.append(listener)

    def _on_agent_activity(self, activity: str) -> None:
        for listener in self.activity_listeners:
            try:
                listener(activity)
            except Exception as e:
                logger.error(f"Error in activity listener: {e}")

    def _pre_augment_intent(self, user_text: str) -> Tuple[str, bool]:
        """Inject real-time telemetry/weather directly into prompt for instant 1-turn response."""
        low = user_text.lower()
        augmented = user_text
        is_augmented = False

        try:
            # 1. Weather / Garmi / Sardi Intent (English + Urdu)
            if any(k in low for k in ["weather", "vedar", "mausam", "temperature", "forecast", "garmi", "sardi", "baarish", "موسم", "بارش", "گرمی", "سردی", "suvidha"]):
                target_city = "auto"
                for city_k, city_v in KNOWN_CITIES.items():
                    if city_k in low:
                        target_city = city_v
                        break

                w_tool = self.registry.get("get_weather")
                if w_tool:
                    res = w_tool.execute(location=target_city)
                    if res.success and isinstance(res.output, dict):
                        augmented += f"\n[Live Real-time Environmental Data for {target_city}: {res.output.get('summary', str(res.output))}]"
                        is_augmented = True

            # 2. Time/Date Intent (English + Urdu)
            elif any(k in low for k in ["what time", "current time", "what's the time", "today's date", "what date", "time kya", "waqt", "وقت", "ٹائم"]):
                t_tool = self.registry.get("get_current_time")
                if t_tool:
                    res = t_tool.execute()
                    if res.success:
                        augmented += f"\n[Live Real-time Clock: {res.output}]"
                        is_augmented = True

            # 3. Hardware / Memory / CPU Intent (English + Urdu)
            elif any(k in low for k in ["cpu usage", "ram usage", "memory usage", "how much ram", "hardware usage", "ram kitni", "cpu kitna", "سسٹم"]):
                m_tool = self.registry.get("get_memory_usage")
                c_tool = self.registry.get("get_cpu_usage")
                if m_tool and c_tool:
                    res_m = m_tool.execute()
                    res_c = c_tool.execute()
                    augmented += f"\n[Live System Telemetry: CPU: {res_c.output}, RAM: {res_m.output}]"
                    is_augmented = True
        except Exception as e:
            logger.debug(f"Intent pre-augmentation skipped: {e}")

        return augmented, is_augmented

    async def handle_user_message(self, user_text: str, speak_response: bool = False) -> AgentResponse:
        """Process a text message from GUI or Voice input end-to-end with high-speed execution."""
        if not user_text.strip():
            return AgentResponse(content="Please provide a query.")

        conv_id = self.active_conversation_id or "default_conv"

        # 1. Store user message in SQLite
        self.memory.add_message(conversation_id=conv_id, role="user", content=user_text)

        # 2. Pre-augment intent with real-time data for instant 1-turn answers
        augmented_text, is_augmented = self._pre_augment_intent(user_text)

        # 3. Retrieve recent message history
        stored_msgs = self.memory.get_messages(conversation_id=conv_id, limit=8)
        history: List[Dict[str, Any]] = [
            {"role": m.role, "content": m.content, "tool_calls": m.tool_calls}
            for m in stored_msgs[:-1]
        ]

        # 4. Assemble prompt context
        messages = self.context_builder.build_context(
            user_input=augmented_text,
            conversation_history=history,
        )

        # 5. Fast-path max tokens: 80 tokens for conversational voice (~1.5s latency)
        max_tokens_override = 80 if is_augmented or speak_response else None

        # 6. Run Agent Loop
        response = await self.agent.run(
            messages=messages,
            include_tools=not is_augmented,
            max_tokens=max_tokens_override,
        )

        # 7. Persist Assistant Response in SQLite
        self.memory.add_message(
            conversation_id=conv_id,
            role="assistant",
            content=response.content,
            tool_calls=[{"tool_name": t.tool_name, "result": t.result} for t in response.tool_traces] if response.tool_traces else None,
        )

        # 8. Speak response if voice output requested
        if speak_response and self.tts and self.config.voice.enabled:
            self.tts.speak(response.content)

        # 9. Notify response listeners
        for listener in self.response_listeners:
            try:
                listener(user_text, response)
            except Exception as e:
                logger.error(f"Error in response listener: {e}")

        return response
