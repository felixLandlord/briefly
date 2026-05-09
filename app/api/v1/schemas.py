from pydantic import BaseModel, Field, field_validator
from app.core.config import settings
from app.core.llm import LLM_OPTIONS


class AnalyseRequest(BaseModel):
    companies: list[str] = Field(
        ...,
        min_length=1,
        max_length=10,
        description="One or more company names to analyse.",
        examples=[["Stripe", "Brex"]],
    )
    thread_id: str | None = Field(
        default=None,
        description="Optional thread ID to resume an existing conversation.",
    )
    orchestrator_model: LLM_OPTIONS | None = Field(
        default=LLM_OPTIONS(settings.default_orchestrator_model),
        description="Model to use for the orchestrator agent.",
    )
    researcher_model: LLM_OPTIONS | None = Field(
        default=LLM_OPTIONS(settings.default_researcher_model),
        description="Model to use for the website-researcher subagent.",
    )
    writer_model: LLM_OPTIONS | None = Field(
        default=LLM_OPTIONS(settings.default_writer_model),
        description="Model to use for the brief-writer subagent.",
    )

    @field_validator("companies")
    @classmethod
    def strip_and_dedupe(cls, v: list[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for name in v:
            stripped = name.strip()
            if stripped and stripped.lower() not in seen:
                seen.add(stripped.lower())
                result.append(stripped)
        if not result:
            raise ValueError("At least one non-empty company name is required.")
        return result


class BriefMeta(BaseModel):
    company: str
    path: str
    size_bytes: int | None = None


class AnalyseResponse(BaseModel):
    """Returned at the end of a non-streaming run (for testing / non-SSE clients)."""

    thread_id: str
    companies: list[str]
    briefs: list[BriefMeta] = Field(default_factory=list)
    summary: str = ""


class BriefListItem(BaseModel):
    company: str
    path: str
    filename: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "0.1.0"