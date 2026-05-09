from fastapi import FastAPI, responses, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager 
from app.api.v1 import routes
from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.tracing import init_langsmith_tracing

setup_logging()
init_langsmith_tracing()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown."""

    logger.info("application_starting")
    yield
    logger.info("application_shutting_down")

app = FastAPI(
    title="Briefly API",
    description="AI-powered Competitive Intelligence System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
async def root() -> responses.RedirectResponse:
    """Redirect to /docs"""
    
    try:
        logger.info("Redirecting to /docs")
        return responses.RedirectResponse("/docs")
    except Exception as e:
        logger.error(f"Error redirecting to /docs: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to redirect to /docs",
        )

app.include_router(routes.router)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )