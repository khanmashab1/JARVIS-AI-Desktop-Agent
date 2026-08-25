"""Core Jarvis Agent implementing the Reason/Act orchestration loop with smart tool schema loading."""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from app.constants import DEFAULT_MAX_ITERATIONS, RiskLevel
from app.providers.llm.base import LLMError, LLMProvider, LLMResponse, ToolCall
from app.security.permissions import PermissionEngine
from app.tools.base import Tool, ToolResult
from app.tools.registry import ToolRegistry
from app.utils.logging import get_logger

logger = get_logger("agent.core")


@dataclass
class ToolExecutionTrace:
    """Audit trace for developer observability mode."""
    tool_name: str
    arguments: Dict[str, Any]
    risk_level: str
    approved: bool
    result: str
    duration_ms: float = 0.0


@dataclass
class AgentResponse:
    """Final response package returned to caller/UI."""
    content: str
    tool_traces: List[ToolExecutionTrace] = field(default_factory=list)
    iterations_used: int = 0
    error: Optional[str] = None


class JarvisAgent:
    """Autonomous desktop agent orchestrating LLM reasoning with safe Python execution."""

    def __init__(
        self,
        llm_provider: LLMProvider,
        tool_registry: ToolRegistry,
        permission_engine: PermissionEngine,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        on_activity: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.llm = llm_provider
        self.registry = tool_registry
        self.permissions = permission_engine
        self.max_iterations = max_iterations
        self.on_activity = on_activity

    def _notify_activity(self, message: str) -> None:
        logger.info(f"AGENT ACTIVITY: {message}")
        if self.on_activity:
            try:
                self.on_activity(message)
            except Exception:
                pass

    async def run(
        self,
        messages: List[Dict[str, Any]],
        include_tools: bool = True,
        **kwargs: Any,
    ) -> AgentResponse:
        """Execute the agent loop until completion or iteration limit."""
        conversation = list(messages)
        traces: List[ToolExecutionTrace] = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            tool_schemas = self.registry.get_schemas() if include_tools else None

            self._notify_activity(f"Consulting AI brain (Iteration {iteration}/{self.max_iterations})...")

            try:
                llm_response = await self.llm.chat(
                    messages=conversation,
                    tools=tool_schemas if (include_tools and tool_schemas) else None,
                    **kwargs,
                )
            except LLMError as le:
                logger.error(f"LLM failure in agent loop: {le}")
                return AgentResponse(
                    content=le.friendly,
                    tool_traces=traces,
                    iterations_used=iteration,
                    error=str(le),
                )
            except Exception as e:
                logger.error(f"Unexpected error in agent reasoning turn: {e}")
                return AgentResponse(
                    content="I encountered an unexpected issue while reasoning about your request.",
                    tool_traces=traces,
                    iterations_used=iteration,
                    error=str(e),
                )

            # If the model produced text and no tool calls, we have our final response
            if not llm_response.has_tool_calls:
                final_text = llm_response.content or "I have processed your request."
                return AgentResponse(
                    content=final_text,
                    tool_traces=traces,
                    iterations_used=iteration,
                )

            # Process requested tool calls
            assistant_msg: Dict[str, Any] = {
                "role": "assistant",
                "content": llm_response.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                    }
                    for tc in llm_response.tool_calls
                ],
            }
            conversation.append(assistant_msg)

            for tool_call in llm_response.tool_calls:
                tool_name = tool_call.name
                args = tool_call.arguments
                tool_id = tool_call.id

                self._notify_activity(f"Selecting tool: {tool_name}")

                tool = self.registry.get(tool_name)
                if not tool:
                    err_msg = f"Tool '{tool_name}' is not registered."
                    logger.warning(err_msg)
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps({"error": err_msg}),
                    })
                    continue

                # Permission & Confirmation Check
                is_approved = self.permissions.check_permission(
                    tool_name=tool.name,
                    risk_level=tool.risk_level,
                    arguments=args,
                    explicit_requires_confirmation=tool.requires_confirmation,
                )
                if not is_approved:
                    self._notify_activity(f"Tool {tool_name} was denied by user.")
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps({"error": "User denied permission to execute this action."}),
                    })
                    traces.append(ToolExecutionTrace(
                        tool_name=tool_name,
                        arguments=args,
                        risk_level=tool.risk_level.value,
                        approved=False,
                        result="Permission denied by user.",
                    ))
                    continue

                self._notify_activity(f"Executing: {tool_name}")
                start_t = asyncio.get_event_loop().time()
                try:
                    tool_result: ToolResult = tool.execute(**args)
                    dur_ms = (asyncio.get_event_loop().time() - start_t) * 1000

                    res_str = str(tool_result.output) if tool_result.success else str(tool_result.error)
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps({
                            "success": tool_result.success,
                            "output": tool_result.output,
                            "error": tool_result.error,
                        }),
                    })
                    traces.append(ToolExecutionTrace(
                        tool_name=tool_name,
                        arguments=args,
                        risk_level=tool.risk_level.value,
                        approved=True,
                        result=res_str[:500],
                        duration_ms=dur_ms,
                    ))
                except Exception as ex:
                    logger.error(f"Error executing tool {tool_name}: {ex}")
                    conversation.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": json.dumps({"error": f"Tool execution failed: {ex}"}),
                    })
                    traces.append(ToolExecutionTrace(
                        tool_name=tool_name,
                        arguments=args,
                        risk_level=tool.risk_level.value,
                        approved=True,
                        result=f"Error: {ex}",
                    ))

        return AgentResponse(
            content="I reached the maximum reasoning iterations without finalizing. Please check the logs.",
            tool_traces=traces,
            iterations_used=iteration,
            error="Max iterations reached",
        )
