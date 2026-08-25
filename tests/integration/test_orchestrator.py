"""Integration tests for JarvisOrchestrator."""

from pathlib import Path
import pytest

from app.agent.orchestrator import JarvisOrchestrator
from app.config import Config
from app.memory.manager import MemoryManager
from app.providers.llm.mock import MockLLMProvider
from app.security.permissions import PermissionEngine
from app.tasks.manager import TaskManager
from app.tools.registry import ToolRegistry
from app.tools.system import GetCurrentTimeTool


@pytest.mark.asyncio
async def test_orchestrator_flow(tmp_path: Path):
    db_file = tmp_path / "orch_test.db"
    cfg = Config()
    cfg.database_path = db_file
    cfg.voice.enabled = False

    memory = MemoryManager(db_file)
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())
    permissions = PermissionEngine()
    tasks = TaskManager(memory_manager=memory)
    mock_llm = MockLLMProvider("Hello! I am ready.")

    orchestrator = JarvisOrchestrator(
        config=cfg,
        llm_provider=mock_llm,
        tool_registry=registry,
        permission_engine=permissions,
        memory_manager=memory,
        task_manager=tasks,
    )

    response = await orchestrator.handle_user_message("Hello JARVIS")
    assert response.content == "Hello! I am ready."

    # Verify conversation stored
    conv_id = orchestrator.active_conversation_id
    msgs = memory.get_messages(conv_id)
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[0].content == "Hello JARVIS"
    assert msgs[1].role == "assistant"
    assert msgs[1].content == "Hello! I am ready."
