"""Integration tests for the Agent Reason/Act loop and multi-step tool execution."""

from pathlib import Path
import pytest

from app.agent.agent import JarvisAgent
from app.constants import RiskLevel
from app.providers.llm.base import LLMResponse, ToolCall
from app.providers.llm.mock import MockLLMProvider
from app.security.permissions import PermissionEngine
from app.security.policies import SecurityPolicy
from app.security.sanitizer import InputSanitizer
from app.tools.filesystem import CreateFileTool, CreateFolderTool, DeleteFileTool
from app.tools.registry import ToolRegistry
from app.tools.system import GetCurrentTimeTool


@pytest.mark.asyncio
async def test_agent_single_tool_execution(tmp_path: Path):
    mock_llm = MockLLMProvider()
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())

    permission_engine = PermissionEngine()
    agent = JarvisAgent(
        llm_provider=mock_llm,
        tool_registry=registry,
        permission_engine=permission_engine,
    )

    # 1. First turn: LLM requests tool call
    mock_llm.queue_response(
        LLMResponse(
            tool_calls=[ToolCall(id="call_time", name="get_current_time", arguments={})]
        )
    )
    # 2. Second turn: LLM provides final answer with tool result
    mock_llm.queue_response(
        LLMResponse(content="The current local time has been retrieved successfully.")
    )

    response = await agent.run(messages=[{"role": "user", "content": "What time is it?"}])

    assert response.content == "The current local time has been retrieved successfully."
    assert len(response.tool_traces) == 1
    assert response.tool_traces[0].tool_name == "get_current_time"
    assert response.tool_traces[0].approved is True


@pytest.mark.asyncio
async def test_agent_multi_step_file_creation(tmp_path: Path):
    mock_llm = MockLLMProvider()
    sanitizer = InputSanitizer(allowed_roots=[tmp_path])
    registry = ToolRegistry()
    registry.register(CreateFolderTool(sanitizer))
    registry.register(CreateFileTool(sanitizer))

    permission_engine = PermissionEngine(sanitizer=sanitizer)
    agent = JarvisAgent(
        llm_provider=mock_llm,
        tool_registry=registry,
        permission_engine=permission_engine,
    )

    target_folder = str(tmp_path / "JARVIS_TEST")
    target_file = str(tmp_path / "JARVIS_TEST" / "hello.py")

    # Step 1: Create folder
    mock_llm.queue_response(
        LLMResponse(
            tool_calls=[ToolCall(id="call_1", name="create_folder", arguments={"path": target_folder})]
        )
    )
    # Step 2: Create file with code
    mock_llm.queue_response(
        LLMResponse(
            tool_calls=[ToolCall(id="call_2", name="create_file", arguments={"path": target_file, "content": "print('Hello JARVIS')\n"})]
        )
    )
    # Step 3: Final response
    mock_llm.queue_response(
        LLMResponse(content="Successfully created folder JARVIS_TEST and file hello.py with starter Python code.")
    )

    response = await agent.run(messages=[{"role": "user", "content": "Create JARVIS_TEST folder and hello.py"}])

    assert "Successfully created folder" in response.content
    assert len(response.tool_traces) == 2
    assert Path(target_folder).exists()
    assert Path(target_file).exists()
    assert "Hello JARVIS" in Path(target_file).read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_agent_respects_user_permission_denial(tmp_path: Path):
    mock_llm = MockLLMProvider()
    sanitizer = InputSanitizer(allowed_roots=[tmp_path])
    registry = ToolRegistry()
    registry.register(DeleteFileTool(sanitizer))

    # User rejects permission dialog
    def reject_dialog(name, desc, risk, args):
        return False

    permission_engine = PermissionEngine(
        policy=SecurityPolicy(),
        sanitizer=sanitizer,
        confirmation_callback=reject_dialog,
    )

    agent = JarvisAgent(
        llm_provider=mock_llm,
        tool_registry=registry,
        permission_engine=permission_engine,
    )

    # 1. LLM requests delete_file
    mock_llm.queue_response(
        LLMResponse(
            tool_calls=[ToolCall(id="call_del", name="delete_file", arguments={"path": str(tmp_path / "data.db")})]
        )
    )
    # 2. LLM responds after seeing rejection
    mock_llm.queue_response(
        LLMResponse(content="The deletion operation was cancelled as per your instruction.")
    )

    response = await agent.run(messages=[{"role": "user", "content": "Delete my database."}])

    assert len(response.tool_traces) == 1
    assert response.tool_traces[0].approved is False
    assert "cancelled" in response.content.lower()


@pytest.mark.asyncio
async def test_agent_iteration_limit():
    mock_llm = MockLLMProvider()
    registry = ToolRegistry()
    registry.register(GetCurrentTimeTool())
    agent = JarvisAgent(
        llm_provider=mock_llm,
        tool_registry=registry,
        permission_engine=PermissionEngine(),
        max_iterations=3,
    )

    # Queue infinite loop of tool calls
    for i in range(10):
        mock_llm.queue_response(
            LLMResponse(tool_calls=[ToolCall(id=f"call_{i}", name="get_current_time", arguments={})])
        )

    response = await agent.run(messages=[{"role": "user", "content": "Loop forever"}])
    assert response.iterations_used == 3
    assert response.error == "Max iterations reached"
