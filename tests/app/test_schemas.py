import pytest
from pydantic import ValidationError
from app.api.v1.schemas import (
    AnalyseRequest,
    BriefMeta,
    AnalyseResponse,
    BriefListItem,
    HealthResponse,
)


class TestAnalyseRequest:
    def test_valid_single_company(self):
        request = AnalyseRequest(companies=["Stripe"])
        assert request.companies == ["Stripe"]
        assert request.thread_id is None
        assert request.orchestrator_model is not None

    def test_valid_multiple_companies(self):
        request = AnalyseRequest(companies=["Stripe", "Brex", "Plaid"])
        assert request.companies == ["Stripe", "Brex", "Plaid"]

    def test_thread_id_optional(self):
        request = AnalyseRequest(companies=["Stripe"], thread_id="abc123")
        assert request.thread_id == "abc123"

    def test_companies_stripped_and_deduplicated(self):
        request = AnalyseRequest(companies=["  Stripe  ", "stripe", "  BREX  "])
        assert request.companies == ["Stripe", "BREX"]

    def test_empty_company_filtered(self):
        request = AnalyseRequest(companies=["Stripe", "  ", ""])
        assert request.companies == ["Stripe"]

    def test_case_insensitive_dedup(self):
        request = AnalyseRequest(companies=["stripe", "Stripe", "STRIPE"])
        assert request.companies == ["stripe"]

    def test_min_length_validation(self):
        with pytest.raises(ValidationError):
            AnalyseRequest(companies=[])

    def test_max_length_validation(self):
        with pytest.raises(ValidationError):
            AnalyseRequest(companies=[f"Company{i}" for i in range(11)])

    def test_at_least_one_non_empty_required(self):
        with pytest.raises(ValidationError):
            AnalyseRequest(companies=["  ", ""])


class TestBriefMeta:
    def test_basic_fields(self):
        meta = BriefMeta(company="stripe", path="/path/to/brief.md")
        assert meta.company == "stripe"
        assert meta.path == "/path/to/brief.md"
        assert meta.size_bytes is None

    def test_with_size_bytes(self):
        meta = BriefMeta(company="stripe", path="/path/to/brief.md", size_bytes=1234)
        assert meta.size_bytes == 1234


class TestAnalyseResponse:
    def test_defaults(self):
        response = AnalyseResponse(thread_id="abc", companies=["Stripe"])
        assert response.thread_id == "abc"
        assert response.companies == ["Stripe"]
        assert response.briefs == []
        assert response.summary == ""

    def test_with_briefs(self):
        response = AnalyseResponse(
            thread_id="abc",
            companies=["Stripe"],
            briefs=[BriefMeta(company="Stripe", path="/path/to/brief.md")],
        )
        assert len(response.briefs) == 1


class TestBriefListItem:
    def test_fields(self):
        item = BriefListItem(company="stripe", path="/path/to/brief.md", filename="brief.md")
        assert item.company == "stripe"
        assert item.filename == "brief.md"


class TestHealthResponse:
    def test_default_status(self):
        response = HealthResponse()
        assert response.status == "ok"
        assert response.version == "0.1.0"
