import os
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def init_langsmith_tracing():
    """Initialize LangSmith tracing if enabled in config."""

    if not settings.langsmith_tracing:
        logger.info("[init_langsmith_tracing] LangSmith tracing disabled")
        return

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint

    logger.info(
        f"[init_langsmith_tracing] LangSmith tracing enabled for project: "
        f"{settings.langsmith_project}"
    )
