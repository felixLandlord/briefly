from langchain_mcp_adapters.client import MultiServerMCPClient
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def build_mcp_config() -> dict:
    """Build the MCP server configuration dict from settings."""
    return {
        "minimax-mcp-server": {
            "command": "uvx",
            "args": ["--quiet", "--no-progress", "minimax-coding-plan-mcp", "-y"],
            "env": {
                "MINIMAX_API_KEY": settings.minimax_api_key,
                "MINIMAX_API_HOST": settings.minimax_api_host.removesuffix("/v1"),
            },
            "transport": "stdio",
        }
    }


async def get_mcp_tools() -> list:
    """
    Return a fresh list of MCP tools.

    This is designed to be passed as `tool_provider` to DeepAgent so the
    harness resolves tools lazily at run-time rather than at import time.
    """
    config = build_mcp_config()
    logger.debug("mcp_client.initialising", servers=list(config.keys()))
    client = MultiServerMCPClient(config)
    tools = await client.get_tools()
    logger.info("mcp_tools_loaded", count=len(tools), tools=[t.name for t in tools])
    return tools