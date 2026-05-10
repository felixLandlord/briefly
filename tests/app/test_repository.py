import pytest
import tempfile
import shutil
from pathlib import Path
from app.core.repository import OutputRepository, _slugify


class TestSlugify:
    def test_converts_to_lowercase(self):
        assert _slugify("STRIPE") == "stripe"

    def test_strips_whitespace(self):
        assert _slugify("  Stripe  ") == "stripe"

    def test_removes_special_characters(self):
        assert _slugify("Pay, Inc!") == "pay-inc"


@pytest.fixture
def temp_repo(tmp_path: Path) -> OutputRepository:
    repo = OutputRepository.__new__(OutputRepository)
    repo.output_dir = tmp_path / "outputs"
    repo.output_dir.mkdir(parents=True, exist_ok=True)
    return repo


@pytest.mark.asyncio
class TestOutputRepository:
    async def test_save_brief(self, temp_repo: OutputRepository):
        content = "# Stripe\n\n## TL;DR\n\nA payment company."
        path = await temp_repo.save_brief("Stripe", content)

        assert path.exists()
        assert path.suffix == ".md"
        assert "stripe" in path.stem

    async def test_save_brief_adds_timestamp(self, temp_repo: OutputRepository):
        content = "# Stripe\n\n## TL;DR\n\nA payment company."
        path = await temp_repo.save_brief("Stripe", content)
        content = await temp_repo.read_brief(path)

        assert "Brief generated:" in content

    async def test_save_brief_no_duplicate_timestamp(self, temp_repo: OutputRepository):
        content = "# Stripe\n\n*Brief generated: 2024-01-01*\n\n## TL;DR"
        path = await temp_repo.save_brief("Stripe", content)
        content = await temp_repo.read_brief(path)

        assert content.count("Brief generated:") == 1

    async def test_list_briefs_empty(self, temp_repo: OutputRepository):
        briefs = await temp_repo.list_briefs()
        assert briefs == []

    async def test_list_briefs_by_company(self, temp_repo: OutputRepository):
        await temp_repo.save_brief("Stripe", "# Stripe content")
        await temp_repo.save_brief("Brex", "# Brex content")
        await temp_repo.save_brief("Stripe", "# Stripe content 2")

        stripe_briefs = await temp_repo.list_briefs("Stripe")
        assert len(stripe_briefs) == 2
        assert all("stripe" in str(p) for p in stripe_briefs)

    async def test_list_briefs_nonexistent_company(self, temp_repo: OutputRepository):
        briefs = await temp_repo.list_briefs("NonExistent")
        assert briefs == []

    async def test_list_briefs_all_companies(self, temp_repo: OutputRepository):
        await temp_repo.save_brief("Stripe", "# Stripe content")
        await temp_repo.save_brief("Brex", "# Brex content")

        briefs = await temp_repo.list_briefs()
        assert len(briefs) == 2

    async def test_read_brief(self, temp_repo: OutputRepository):
        original_content = "# Stripe\n\n## TL;DR\n\nA payment company."
        path = await temp_repo.save_brief("Stripe", original_content)
        content = await temp_repo.read_brief(path)

        assert "Stripe" in content

    async def test_brief_path_creates_company_dir(self, temp_repo: OutputRepository):
        path = temp_repo._brief_path("Stripe", "abc12345")
        
        assert path.parent.name == "stripe"
        assert path.parent.parent == temp_repo.output_dir
