from deepagents import create_deep_agent
from langchain_core.language_models import BaseChatModel
from app.agents.subagents import get_subagents
from app.agents.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from app.agents.mcp import get_mcp_tools
from app.agents.tools import tavily_search
from app.core.llm import LLM, LLM_OPTIONS
from app.core.middleware import log_tool_calls
from app.core.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


def _build_llm(model: LLM_OPTIONS) -> BaseChatModel:
    return LLM().get_llm(model)


async def create_orchestrator(
    orchestrator_model: LLM_OPTIONS = LLM_OPTIONS(settings.default_orchestrator_model),
    researcher_model: LLM_OPTIONS = LLM_OPTIONS(settings.default_researcher_model),
    writer_model: LLM_OPTIONS = LLM_OPTIONS(settings.default_writer_model),
):
    """
    Build and return the main orchestration DeepAgent with configurable subagents.
    """
    
    # 1. Build LLMs for everyone
    orc_llm = _build_llm(orchestrator_model)
    res_llm = _build_llm(researcher_model)
    wri_llm = _build_llm(writer_model)

    logger.info(
        "orchestrator.creating",
        orchestrator_model=orchestrator_model.base_model,
        researcher_model=researcher_model.base_model,
        writer_model=writer_model.base_model,
    )

    # 2. Resolve tools (MCP tools are async)
    mcp_tools = await get_mcp_tools()
    
    # 3. Select search provider: MiniMax models use MCP tools, others use Tavily
    research_tools = list(mcp_tools)
    if not researcher_model.is_minimax:
        research_tools.append(tavily_search)

    # 4. Resolve subagents with their specific LLMs and tools
    subagents = get_subagents(
        researcher_llm=res_llm,
        writer_llm=wri_llm,
        research_tools=research_tools,
    )

    # 5. Create the deep agent
    agent = create_deep_agent(
        model=orc_llm,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        subagents=subagents,
        tools=[],  # Orchestrator should only have subagents, no direct tools
        middleware=[log_tool_calls],
        name="orchestrator",
    )

    logger.info("orchestrator.ready")
    return agent