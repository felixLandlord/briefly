import time
from langchain.agents.middleware import wrap_tool_call
from app.core.logging import get_logger

logger = get_logger(__name__)


_call_count: list[int] = [0]

@wrap_tool_call  # type: ignore
async def log_tool_calls(request: object, handler: object) -> object:
    """Middleware that logs every tool invocation with timing and agent metadata."""
    _call_count[0] += 1
    current_call = _call_count[0]

    tool_call: dict = getattr(request, "tool_call", {})
    tool_name: str = tool_call.get("name", "unknown")
    tool_args: dict = tool_call.get("args", {})

    runtime = getattr(request, "runtime", None)
    config: dict = getattr(runtime, "config", {}) if runtime else getattr(request, "config", {})
    agent_name: str = config.get("metadata", {}).get("lc_agent_name", "main-agent")

    logger.info(
        "tool_call_started",
        agent_name=agent_name,
        tool_name=tool_name,
        tool_args=tool_args,
        call_number=current_call,
    )

    start = time.perf_counter()
    result = await handler(request)
    duration = round(time.perf_counter() - start, 3)

    logger.info(
        "tool_call_completed",
        agent_name=agent_name,
        tool_name=tool_name,
        call_number=current_call,
        duration_seconds=duration,
    )
    return result