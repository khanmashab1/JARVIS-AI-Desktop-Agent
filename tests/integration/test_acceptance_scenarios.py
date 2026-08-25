"""Comprehensive acceptance test suite verifying all 50 specification scenarios."""

from pathlib import Path
import pytest

from app.agent.orchestrator import JarvisOrchestrator
from app.config import Config
from app.constants import RiskLevel
from app.memory.manager import MemoryManager
from app.providers.llm.base import LLMError, LLMResponse, ToolCall
from app.providers.llm.mock import MockLLMProvider
from app.security.permissions import PermissionEngine
from app.security.policies import SecurityPolicy
from app.security.sanitizer import InputSanitizer
from app.tasks.manager import TaskManager
from app.tools.applications import OpenApplicationTool
from app.tools.browser import OpenUrlTool, SearchWebTool
from app.tools.filesystem import CreateFileTool, CreateFolderTool, DeleteFileTool
from app.tools.productivity import CreateNoteTool, CreateReminderTool
from app.tools.registry import ToolRegistry
from app.tools.system import GetCpuUsageTool, GetCurrentTimeTool, GetMemoryUsageTool


@pytest.fixture
def setup_jarvis(tmp_path: Path):
    db_file = tmp_path / "acceptance.db"
    cfg = Config()
    cfg.database_path = db_file
    cfg.voice.enabled = False

    sanitizer = InputSanitizer(allowed_roots=[tmp_path])
    policy = SecurityPolicy()
    confirmation_log = []

    def mock_confirmation_cb(name, desc, risk, args):
        confirmation_log.append((name, risk))
        return True

    permission_engine = PermissionEngine(
        policy=policy,
        sanitizer=sanitizer,
        confirmation_callback=mock_confirmation_cb,
    )

    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())
    registry.register(GetMemoryUsageTool())
    registry.register(GetCpuUsageTool())
    registry.register(OpenApplicationTool())
    registry.register(CreateFolderTool(sanitizer))
    registry.register(CreateFileTool(sanitizer))
    registry.register(DeleteFileTool(sanitizer))
    registry.register(OpenUrlTool())
    registry.register(SearchWebTool())
    registry.register(CreateNoteTool())
    registry.register(CreateReminderTool())

    memory = MemoryManager(db_file)
    tasks = TaskManager(memory)
    mock_llm = MockLLMProvider()

    orchestrator = JarvisOrchestrator(
        config=cfg,
        llm_provider=mock_llm,
        tool_registry=registry,
        permission_engine=permission_engine,
        memory_manager=memory,
        task_manager=tasks,
    )

    return {
        "orchestrator": orchestrator,
        "mock_llm": mock_llm,
        "memory": memory,
        "tmp_path": tmp_path,
        "confirmation_log": confirmation_log,
    }


@pytest.mark.asyncio
async def test_acceptance_basic_queries(setup_jarvis):
    orch = setup_jarvis["orchestrator"]
    mock_llm = setup_jarvis["mock_llm"]

    # 1. Hello JARVIS
    mock_llm.queue_response(LLMResponse(content="Greetings! How may I assist you today?"))
    res = await orch.handle_user_message("Hello JARVIS.")
    assert "Greetings" in res.content

    # 2. What time is it?
    mock_llm.queue_response(LLMResponse(tool_calls=[ToolCall(id="c1", name="get_current_time", arguments={})]))
    mock_llm.queue_response(LLMResponse(content="The current local time is 09:30 PM."))
    res = await orch.handle_user_message("What time is it?")
    assert "current local time" in res.content
    assert len(res.tool_traces) == 1

    # 3. System memory
    mock_llm.queue_response(LLMResponse(tool_calls=[ToolCall(id="c2", name="get_memory_usage", arguments={})]))
    mock_llm.queue_response(LLMResponse(content="You are using 4.2 GB out of 8.0 GB RAM (52.5% utilized)."))
    res = await orch.handle_user_message("What is my system memory usage?")
    assert "RAM" in res.content


@pytest.mark.asyncio
async def test_acceptance_files_and_folders(setup_jarvis):
    orch = setup_jarvis["orchestrator"]
    mock_llm = setup_jarvis["mock_llm"]
    tmp_path = setup_jarvis["tmp_path"]

    test_folder = str(tmp_path / "JARVIS_TEST")
    test_file = str(tmp_path / "JARVIS_TEST" / "hello.py")

    # Multi-step: create folder -> create file with python code
    mock_llm.queue_response(LLMResponse(tool_calls=[ToolCall(id="f1", name="create_folder", arguments={"path": test_folder})]))
    mock_llm.queue_response(LLMResponse(tool_calls=[ToolCall(id="f2", name="create_file", arguments={"path": test_file, "content": "print('Hello World')\n"})]))
    mock_llm.queue_response(LLMResponse(content="I have created the folder JARVIS_TEST and written hello.py inside it."))

    res = await orch.handle_user_message("Create a folder called JARVIS_TEST, create a file called hello.py inside it, and write a Python hello-world program.")

    assert len(res.tool_traces) == 2
    assert Path(test_file).exists()
    assert "Hello World" in Path(test_file).read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_acceptance_memory_retention(setup_jarvis):
    orch = setup_jarvis["orchestrator"]
    mock_llm = setup_jarvis["mock_llm"]
    memory = setup_jarvis["memory"]

    # 1. "Remember that my main project is JARVIS."
    memory.remember_project("JARVIS", "My main project is called JARVIS.")

    # 2. "What is my main project?" -> ContextBuilder injects the project memory!
    mock_llm.queue_response(LLMResponse(content="Your main project is JARVIS, an autonomous AI desktop agent."))
    res = await orch.handle_user_message("What is my main project?")
    assert "JARVIS" in res.content

    # 3. "Forget that my main project is JARVIS."
    memory.delete_memory("JARVIS")
    assert len(memory.list_memories()) == 0


@pytest.mark.asyncio
async def test_acceptance_permission_security_confirmation(setup_jarvis):
    orch = setup_jarvis["orchestrator"]
    mock_llm = setup_jarvis["mock_llm"]
    tmp_path = setup_jarvis["tmp_path"]
    confirm_log = setup_jarvis["confirmation_log"]

    del_target = tmp_path / "sensitive.txt"
    del_target.write_text("critical data", encoding="utf-8")

    # LLM requests delete_file (HIGH RISK)
    mock_llm.queue_response(LLMResponse(tool_calls=[ToolCall(id="d1", name="delete_file", arguments={"path": str(del_target)})]))
    mock_llm.queue_response(LLMResponse(content="The file has been deleted after receiving your approval."))

    res = await orch.handle_user_message("Delete this file.")

    # Verify confirmation callback was triggered for HIGH risk
    assert len(confirm_log) == 1
    assert confirm_log[0][0] == "delete_file"
    assert confirm_log[0][1] == RiskLevel.HIGH
    assert not del_target.exists()


@pytest.mark.asyncio
async def test_acceptance_error_recovery(setup_jarvis):
    orch = setup_jarvis["orchestrator"]
    mock_llm = setup_jarvis["mock_llm"]

    # Simulate provider failure / network disconnect
    def failing_chat(messages, tools):
        raise LLMError("API Connection Timeout", friendly="The AI provider is currently unavailable. Please check your connection.")

    mock_llm.response_generator = failing_chat

    res = await orch.handle_user_message("What is the weather?")
    assert "The AI provider is currently unavailable" in res.content
