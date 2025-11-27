from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Gemini API Configuration
    gemini_api_key: str

    # File Upload Configuration
    max_file_size: int = 15 * 1024 * 1024  # 15 MB in bytes
    allowed_extensions: list[str] = ["pdf", "docx", "txt", "doc", "md"]
    allowed_mime_types: list[str] = [
        "application/pdf",
        "text/plain",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "text/markdown",
        "text/x-markdown",
    ]


# Global settings instance
settings = Settings()
