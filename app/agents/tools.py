from langchain_core.tools import tool
from tavily import TavilyClient

from app.core.config import settings
from app.core.repository import output_repository


@tool
async def save_brief(company_name: str, content: str) -> str:
    """
    Save a competitive intelligence brief to disk.

    Args:
        company_name: The canonical name of the company (e.g. "Stripe").
        content:      The full GitHub-flavoured Markdown brief.

    Returns:
        The absolute file path where the brief was saved.
    """
    path = await output_repository.save_brief(company_name, content)
    return str(path.resolve())


@tool
def tavily_search(
    query: str,
    max_results: int = 10,
    include_raw_content: bool = False,
) -> dict:
    """
    Run a high-quality web search to gather competitive intelligence.
    Use this for finding company taglines, pricing, news, and job roles.
    """
    client = TavilyClient(api_key=settings.tavily_api_key)
    return client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        search_depth="advanced",
    )