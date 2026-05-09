"""
Dict-based subagent specs following the DeepAgents SubAgent schema.
These are plain dicts so they're easy to inspect, test, and patch.
"""
from typing import Any
from langchain_core.language_models import BaseChatModel

from app.agents.tools import save_brief
from app.agents.prompts import (
    BRIEF_WRITER_SYSTEM_PROMPT,
    WEBSITE_RESEARCHER_SYSTEM_PROMPT,
)


def get_subagents(
    researcher_llm: BaseChatModel,
    writer_llm: BaseChatModel,
) -> list[dict[str, Any]]:
    """
    Return a list of subagent specifications with the provided LLMs.
    """
    
    website_researcher: dict[str, Any] = {
        "name": "website-researcher",
        "description": (
            "Researches a single company's official website, news, job postings, and "
            "pricing pages to gather raw competitive intelligence. Give it a company name."
        ),
        "system_prompt": WEBSITE_RESEARCHER_SYSTEM_PROMPT,
        "model": researcher_llm,
        # Inherits both search tools from the orchestrator
    }

    brief_writer: dict[str, Any] = {
        "name": "brief-writer",
        "description": (
            "Transforms raw company research data into a polished GitHub-flavoured "
            "Markdown competitive brief and saves it to disk. Pass the full research "
            "result from the website-researcher."
        ),
        "system_prompt": BRIEF_WRITER_SYSTEM_PROMPT,
        "tools": [save_brief],
        "model": writer_llm,
    }

    return [website_researcher, brief_writer]