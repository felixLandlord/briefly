from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # App
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    output_dir: Path = Field(default=Path("outputs"), alias="OUTPUT_DIR")

    # Default Models
    default_orchestrator_model: str = Field(default="MiniMax-M2.7", alias="DEFAULT_ORCHESTRATOR_MODEL")
    default_researcher_model: str = Field(default="MiniMax-M2.7", alias="DEFAULT_RESEARCHER_MODEL")
    default_writer_model: str = Field(default="MiniMax-M2.7", alias="DEFAULT_WRITER_MODEL")

    # CORS / server
    cors_origins: list[str] = Field(default=["http://localhost:3000", "http://localhost:5173"])
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # MiniMax
    minimax_api_key: str = Field(default="", alias="MINIMAX_API_KEY")
    minimax_api_host: str = Field(default="https://api.minimax.io/v1", alias="MINIMAX_API_HOST")

    # Anthropic
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")

    # Tavily
    tavily_api_key: str = Field(default="", alias="TAVILY_API_KEY")

    # Inception (mercury)
    inception_api_key: str = Field(default="", alias="INCEPTION_API_KEY")
    inception_api_host: str = Field(default="https://api.inceptionlabs.ai/v1", alias="INCEPTION_API_HOST")

    # Langsmith tracing
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_project: str = Field(default="briefly", alias="LANGSMITH_PROJECT")
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    def ensure_output_dir(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()