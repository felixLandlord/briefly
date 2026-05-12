import json
import uuid
from typing import AsyncIterator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.agents.orchestrator import create_orchestrator
from app.api.v1.schemas import AnalyseRequest, HealthResponse
from app.core.repository import output_repository, _slugify
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

    # Extract agent name from namespace if possible
    # ns typically looks like ('orchestrator',) or ('orchestrator', 'tools:website-researcher', ...)
    agent_name = "orchestrator"
    for part in reversed(ns):
        s_part = str(part)
        if s_part.startswith("tools:"):
            agent_name = s_part.replace("tools:", "")
            break
        elif s_part != "orchestrator" and ":" not in s_part:
            # This might be a subagent name without the tools: prefix
            agent_name = s_part
            break

    is_subagent = any(str(s).startswith("tools:") for s in ns)
    source = "subagent" if is_subagent else "main"

    if chunk_type == "messages":
        token, _meta = data  # type: ignore[misc]
        raw_content = getattr(token, "content", "")
        if isinstance(raw_content, dict):
            content = raw_content.get("text", "") or raw_content.get("content", "")
        else:
            content = str(raw_content) if raw_content else ""
        if not content:
            return None
        payload = json.dumps(
            {"source": source, "agent_name": agent_name, "content": content, "ns": list(ns)}
        )
        return _sse_line("token", payload)

    elif chunk_type == "updates":
        node_updates: dict = data  # type: ignore[assignment]
        for node_name in node_updates:
            if node_name in ("model_request", "tools"):
                tool_calls = []
                if node_name == "tools":
                    # Try to extract tool names from the update data
                    # In LangGraph/DeepAgents, 'tools' node update often contains messages with tool_calls
                    node_data = node_updates.get(node_name, {})
                    if isinstance(node_data, dict):
                        msgs = node_data.get("messages", [])
                        for msg in msgs:
                            if hasattr(msg, "tool_calls"):
                                for tc in msg.tool_calls:
                                    tool_calls.append({
                                        "name": tc.get("name"),
                                        "args": tc.get("args")
                                    })

                payload = json.dumps(
                    {
                        "source": source,
                        "agent_name": agent_name,
                        "node": node_name,
                        "ns": list(ns),
                        "tool_calls": tool_calls
                    }
                )
                return _sse_line("update", payload)
        return None

    elif chunk_type == "custom":
        payload = json.dumps(
            {"source": source, "agent_name": agent_name, "data": data, "ns": list(ns)}
        )
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
                if not paths:
                    # Fallback: search all briefs and see if any were created in the last 2 minutes
                    # that might match the company name
                    all_paths = await output_repository.list_briefs(None)
                    # This is a bit fuzzy but helps if the slug changed slightly
                    from datetime import datetime, timedelta
                    import os
                    now = datetime.now()
                    for p in all_paths:
                        if (now - datetime.fromtimestamp(os.path.getmtime(p))).total_seconds() < 120:
                             if company.lower() in p.name.lower():
                                 paths.append(p)
                                 break

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
            log.info("analysis.completed", brief_count=len(briefs), briefs=[b["filename"] for b in briefs])

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
    selected_path = None

    if filename:
        if paths:
            for p in paths:
                if p.name == filename:
                    selected_path = p
                    break
        if not selected_path:
            slug = _slugify(company)
            fallback_path = output_repository.output_dir / slug / filename
            if fallback_path.exists():
                selected_path = fallback_path
                logger.info("get_brief_fallback_path", path=str(fallback_path))

    if not selected_path and paths:
        selected_path = paths[0]

    if not selected_path:
        raise HTTPException(status_code=404, detail=f"No brief found for '{company}'")

    content = await output_repository.read_brief(selected_path)
    return {
        "company": company,
        "filename": selected_path.name,
        "path": str(selected_path),
        "content": content,
    }