import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app
from app.core.repository import OutputRepository


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


class TestAnalyseRequestValidation:
    def test_valid_request_body_structure(self):
        from app.api.v1.schemas import AnalyseRequest
        
        request = AnalyseRequest(
            companies=["Stripe", "Brex"],
            thread_id=None,
        )
        assert len(request.companies) == 2

    def test_model_override_options(self):
        from app.api.v1.schemas import AnalyseRequest
        from app.core.llm import LLM_OPTIONS
        
        request = AnalyseRequest(
            companies=["Stripe"],
            orchestrator_model=LLM_OPTIONS.CLAUDE_SONNET_4_6,
            researcher_model=LLM_OPTIONS.GPT_5_MINI,
            writer_model=LLM_OPTIONS.MINIMAX_2_7,
        )
        assert request.orchestrator_model == LLM_OPTIONS.CLAUDE_SONNET_4_6
        assert request.researcher_model == LLM_OPTIONS.GPT_5_MINI
        assert request.writer_model == LLM_OPTIONS.MINIMAX_2_7


class TestOutputRepository:
    def test_slugify_consistency(self, temp_output_dir: Path):
        repo = OutputRepository.__new__(OutputRepository)
        repo.output_dir = temp_output_dir
        
        slug1 = repo._brief_path("Stripe", "abc12345")
        slug2 = repo._brief_path("stripe", "def67890")
        
        assert slug1.parent.name == slug2.parent.name == "stripe"

    @pytest.mark.asyncio
    async def test_save_and_retrieve_brief(self, temp_output_dir: Path):
        repo = OutputRepository.__new__(OutputRepository)
        repo.output_dir = temp_output_dir
        
        content = "# Test Company\n\n## TL;DR\n\nTest content."
        path = await repo.save_brief("TestCompany", content)
        
        assert path.exists()
        
        retrieved = await repo.read_brief(path)
        assert "Test Company" in retrieved

    @pytest.mark.asyncio
    async def test_list_briefs_sorted_by_newest(self, temp_output_dir: Path):
        repo = OutputRepository.__new__(OutputRepository)
        repo.output_dir = temp_output_dir
        
        await repo.save_brief("Stripe", "# First brief")
        await repo.save_brief("Stripe", "# Second brief")
        
        briefs = await repo.list_briefs("Stripe")
        
        assert len(briefs) == 2
        assert briefs[0].name > briefs[1].name


class TestAPIIntegration:
    def test_openapi_schema_includes_endpoints(self, client: TestClient):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        schema = response.json()
        paths = schema.get("paths", {})
        
        assert "/health" in paths
        assert "/briefs" in paths
        assert "/briefs/{company}" in paths

    def test_cors_headers_configured(self, client: TestClient):
        response = client.options("/health", headers={"Origin": "http://localhost:3000"})
        assert "access-control-allow-origin" in response.headers or response.status_code == 200


class TestBriefPersistence:
    @pytest.mark.asyncio
    async def test_brief_includes_generation_metadata(self, temp_output_dir: Path):
        repo = OutputRepository.__new__(OutputRepository)
        repo.output_dir = temp_output_dir
        
        content = "# Stripe\n\n## Overview\n\nPayment company."
        path = await repo.save_brief("Stripe", content)
        
        content = await repo.read_brief(path)
        assert "Brief generated:" in content
        assert "UTC" in content

    @pytest.mark.asyncio
    async def test_company_directory_structure(self, temp_output_dir: Path):
        repo = OutputRepository.__new__(OutputRepository)
        repo.output_dir = temp_output_dir
        
        await repo.save_brief("Stripe", "# Stripe content")
        await repo.save_brief("Brex", "# Brex content")
        
        stripe_dir = temp_output_dir / "stripe"
        brex_dir = temp_output_dir / "brex"
        
        assert stripe_dir.exists()
        assert brex_dir.exists()


class TestLLMFactory:
    def test_llm_options_has_all_providers(self):
        from app.core.llm import LLM_OPTIONS
        
        assert any(opt.is_anthropic for opt in LLM_OPTIONS)
        assert any(opt.is_openai for opt in LLM_OPTIONS)
        assert any(opt.is_inception for opt in LLM_OPTIONS)
        assert any(opt.is_minimax for opt in LLM_OPTIONS)