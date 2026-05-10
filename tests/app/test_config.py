import pytest
from pathlib import Path
from app.core.config import Settings
from app.core.repository import _slugify


class TestSlugify:
    def test_lowercase(self):
        assert _slugify("Stripe") == "stripe"
        assert _slugify("STRIPE") == "stripe"

    def test_strip_whitespace(self):
        assert _slugify("  Stripe  ") == "stripe"

    def test_remove_special_chars(self):
        assert _slugify("PayPal") == "paypal"
        assert _slugify("Stripe, Inc.") == "stripe-inc"

    def test_hyphenate_spaces(self):
        assert _slugify("Stripe Labs") == "stripe-labs"
        assert _slugify("Stripe_Labs") == "stripe-labs"

    def test_multiple_spaces_become_single_hyphen(self):
        assert _slugify("Stripe  Labs") == "stripe-labs"

    def test_strip_leading_trailing_hyphens(self):
        assert _slugify("-stripe-") == "stripe"


class TestSettings:
    def test_defaults(self):
        settings = Settings()
        assert settings.app_env == "development"
        assert settings.log_level == "INFO"
        assert settings.output_dir == Path("outputs")

    def test_is_development_true_for_default(self):
        settings = Settings()
        assert settings.is_development is True

    def test_default_models(self):
        settings = Settings()
        assert settings.default_orchestrator_model == "MiniMax-M2.7"
        assert settings.default_researcher_model == "MiniMax-M2.7"
        assert settings.default_writer_model == "MiniMax-M2.7"

    def test_cors_origins_default(self):
        settings = Settings()
        assert "http://localhost:3000" in settings.cors_origins
        assert "http://localhost:5173" in settings.cors_origins

    def test_server_defaults(self):
        settings = Settings()
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000

    def test_minimax_api_host_default(self):
        settings = Settings()
        assert settings.minimax_api_host == "https://api.minimax.io/v1"

    def test_tracing_defaults(self):
        settings = Settings()
        assert settings.langsmith_tracing is False
        assert settings.langsmith_project == "briefly"