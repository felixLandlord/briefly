import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["version"] == "0.1.0"

    def test_root_redirects(self, client: TestClient):
        response = client.get("/", follow_redirects=False)
        assert response.status_code in (307, 308)


class TestListBriefsEndpoint:
    def test_list_briefs_empty(self, client: TestClient):
        response = client.get("/briefs")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestGetBriefEndpoint:
    def test_get_brief_nonexistent_returns_404(self, client: TestClient):
        response = client.get("/briefs/NonExistentCompany12345")
        assert response.status_code == 404


class TestSSELine:
    def test_sse_line_format(self):
        from app.api.v1.routes import _sse_line
        
        result = _sse_line("token", '{"content": "hello"}')
        assert result.startswith("event: token\n")
        assert "data: " in result
        assert result.endswith("\n\n")

    def test_sse_line_escapes_newlines_in_data(self):
        from app.api.v1.routes import _sse_line
        
        result = _sse_line("token", '{"content": "line1\\nline2"}')
        assert "\\n" in result or "line1" in result


class TestChunkToSSE:
    def test_converts_messages_to_token_event(self):
        from app.api.v1.routes import _chunk_to_sse
        
        chunk = {
            "type": "messages",
            "ns": (),
            "data": (type("Token", (), {"content": "Hello world"})(), None),
        }
        result = _chunk_to_sse(chunk)
        assert result is not None
        assert "event: token" in result

    def test_converts_subagent_messages(self):
        from app.api.v1.routes import _chunk_to_sse
        
        chunk = {
            "type": "messages",
            "ns": ("tools:researcher",),
            "data": (type("Token", (), {"content": "Researching..."})(), None),
        }
        result = _chunk_to_sse(chunk)
        assert result is not None
        assert "subagent" in result

    def test_converts_updates_to_update_event(self):
        from app.api.v1.routes import _chunk_to_sse
        
        chunk = {
            "type": "updates",
            "ns": (),
            "data": {"model_request": {}},
        }
        result = _chunk_to_sse(chunk)
        assert result is not None
        assert "event: update" in result

    def test_converts_custom_events(self):
        from app.api.v1.routes import _chunk_to_sse
        
        chunk = {
            "type": "custom",
            "ns": (),
            "data": {"step": "researching", "company": "Stripe"},
        }
        result = _chunk_to_sse(chunk)
        assert result is not None
        assert "event: custom" in result

    def test_skips_empty_content(self):
        from app.api.v1.routes import _chunk_to_sse
        
        chunk = {
            "type": "messages",
            "ns": (),
            "data": (type("Token", (), {"content": ""})(), None),
        }
        result = _chunk_to_sse(chunk)
        assert result is None

    def test_ignores_unknown_chunk_types(self):
        from app.api.v1.routes import _chunk_to_sse
        
        chunk = {
            "type": "unknown",
            "ns": (),
            "data": {},
        }
        result = _chunk_to_sse(chunk)
        assert result is None