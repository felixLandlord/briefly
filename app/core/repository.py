import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
import aiofiles
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _slugify(name: str) -> str:
    """Convert a company name to a safe directory/file slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug.strip("-")


class OutputRepository:
    """Handles persisting competitive briefs to the outputs/ directory."""

    def __init__(self) -> None:
        self.output_dir = settings.output_dir
        settings.ensure_output_dir()

    def _brief_path(self, company_name: str, run_id: str) -> Path:
        slug = _slugify(company_name)
        company_dir = self.output_dir / slug
        company_dir.mkdir(parents=True, exist_ok=True)
        return company_dir / f"{slug}-{run_id[:8]}.md"

    async def save_brief(self, company_name: str, content: str) -> Path:
        """Persist a brief and return its path."""
        run_id = uuid.uuid4().hex
        path = self._brief_path(company_name, run_id)

        # Inject generation timestamp into front-matter if not already present
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        if "*Brief generated:" not in content:
            content = content.rstrip() + f"\n\n---\n*Brief generated: {timestamp}*\n"

        async with aiofiles.open(path, "w", encoding="utf-8") as f:
            await f.write(content)

        logger.info(
            "brief_saved",
            company=company_name,
            path=str(path),
            bytes=len(content.encode()),
        )
        return path

    async def list_briefs(self, company_name: str | None = None) -> list[Path]:
        """List all saved briefs, optionally filtered by company."""
        if company_name:
            slug = _slugify(company_name)
            company_dir = self.output_dir / slug
            if not company_dir.exists():
                return []
            return sorted(company_dir.glob("*.md"), reverse=True)
        return sorted(self.output_dir.rglob("*.md"), reverse=True)

    async def read_brief(self, path: Path) -> str:
        async with aiofiles.open(path, encoding="utf-8") as f:
            return await f.read()


output_repository = OutputRepository()
