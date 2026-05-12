import json
import uuid
from typing import AsyncIterator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.agents.orchestrator import create_orchestrator
from app.api.v1.schemas import AnalyseRequest, HealthResponse
from app.core.repository import output_repository
from app.core.logging import get_logger

logger = get_logger(__name__)


router = APIRouter()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def _sse_line(event: str, data: str) -> str:
    """Format a single SSE frame."""
    payload = data.replace("\n", "\\n")
    return f"event: {event}\ndata: {payload}\n\n"


def _chunk_to_sse(chunk: dict) -> str | None:
    """
    Convert a DeepAgents v2 stream chunk to an SSE frame.

    We emit three event types:
    - `token`   — a text token from main or sub agent
    - `update`  — a node-level step update
    - `custom`  — any custom writer event
    - `end`     — sentinel to signal stream completion
    """
    chunk_type: str = chunk.get("type", "")
    ns: tuple = chunk.get("ns", ())
    data: object = chunk.get("data", {})

    is_subagent = any(str(s).startswith("tools:") for s in ns)
    source = "subagent" if is_subagent else "main"

    if chunk_type == "messages":
        token, _meta = data  # type: ignore[misc]
        content = getattr(token, "content", "")
        if not content:
            return None
        payload = json.dumps({"source": source, "content": content, "ns": list(ns)})
        return _sse_line("token", payload)

    elif chunk_type == "updates":
        node_updates: dict = data  # type: ignore[assignment]
        for node_name in node_updates:
            if node_name in ("model_request", "tools"):
                payload = json.dumps(
                    {"source": source, "node": node_name, "ns": list(ns)}
                )
                return _sse_line("update", payload)
        return None

    elif chunk_type == "custom":
        payload = json.dumps({"source": source, "data": data, "ns": list(ns)})
        return _sse_line("custom", payload)

    return None


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.post("/analyse")
async def analyse(request: AnalyseRequest) -> StreamingResponse:
    """
    Kick off competitive intelligence analysis for one or more companies.

    Streams SSE events:
    - `token`  — LLM text tokens (main agent + each subagent)
    - `update` — agent step changes (model_request, tools node)
    - `custom` — custom progress events
    - `end`    — stream finished sentinel with summary data
    """
    thread_id = request.thread_id or uuid.uuid4().hex
    companies_str = ", ".join(request.companies)
    user_message = (
        f"Please analyse the following {'companies' if len(request.companies) > 1 else 'company'} "
        f"and produce a competitive brief for each: {companies_str}"
    )

    log = logger.bind(thread_id=thread_id, companies=request.companies)
    log.info("analysis.started")

    async def event_stream() -> AsyncIterator[str]:
        # Build orchestrator with optional model overrides from request
        model_kwargs = {}
        if request.orchestrator_model:
            model_kwargs["orchestrator_model"] = request.orchestrator_model
        if request.researcher_model:
            model_kwargs["researcher_model"] = request.researcher_model
        if request.writer_model:
            model_kwargs["writer_model"] = request.writer_model

        agent = await create_orchestrator(**model_kwargs)
        try:
            async for chunk in agent.astream(  # type: ignore[attr-defined]
                {"messages": [{"role": "user", "content": user_message}]},
                stream_mode=["updates", "messages", "custom"],
                subgraphs=True,
                version="v2",
            ):
                sse = _chunk_to_sse(chunk)
                if sse:
                    yield sse

            # Collect generated briefs for the end payload
            briefs = []
            for company in request.companies:
                paths = await output_repository.list_briefs(company)
                for p in paths[:1]:  # most recent
                    briefs.append(
                        {
                            "company": company,
                            "path": str(p),
                            "filename": p.name,
                        }
                    )

            end_payload = json.dumps(
                {
                    "thread_id": thread_id,
                    "companies": request.companies,
                    "briefs": briefs,
                }
            )
            yield _sse_line("end", end_payload)
            log.info("analysis.completed", brief_count=len(briefs))

        except Exception as exc:
            log.exception("analysis.error", error=str(exc))
            error_payload = json.dumps({"error": str(exc)})
            yield _sse_line("error", error_payload)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/briefs")
async def list_briefs(company: str | None = None) -> list[dict]:
    """List saved briefs, optionally filtered by company name."""
    logger.info("list_briefs_requested", company=company)
    paths = await output_repository.list_briefs(company)
    return [
        {
            "company": p.parent.name,
            "path": str(p),
            "filename": p.name,
        }
        for p in paths
    ]


@router.get("/briefs/{company}")
async def get_brief(company: str, filename: str | None = None) -> dict:
    """Return a brief for a company, optionally a specific filename."""
    logger.info("get_brief_requested", company=company, filename=filename)
    paths = await output_repository.list_briefs(company)
    if not paths:
        raise HTTPException(status_code=404, detail=f"No briefs found for '{company}'")

    selected_path = paths[0]
    if filename:
        for p in paths:
            if p.name == filename:
                selected_path = p
                break
        else:
            raise HTTPException(
                status_code=404, detail=f"Brief '{filename}' not found for '{company}'"
            )

    content = await output_repository.read_brief(selected_path)
    return {
        "company": company,
        "filename": selected_path.name,
        "path": str(selected_path),
        "content": content,
    }