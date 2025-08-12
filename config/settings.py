"""Configuration settings for SIVA application."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class SivaSettings(BaseSettings):
    """SIVA application settings using Pydantic BaseSettings."""

    # API Keys
    openai_api_key: str = Field(..., description="OpenAI API key for chat and STT")
    cartesia_api_key: str = Field(..., description="Cartesia API key for TTS")

    # FastAPI Configuration
    app_host: str = Field(default="localhost", description="FastAPI host")
    app_port: int = Field(default=8000, description="FastAPI port")
    app_reload: bool = Field(default=True, description="FastAPI auto-reload")
    app_debug: bool = Field(default=False, description="Debug mode")

    # Client Server Configuration
    client_host: str = Field(default="localhost", description="Client server host")
    client_port: int = Field(default=3000, description="Client server port")

    # Vector Store Configuration
    retrieval_threshold: int = Field(
        default=3, description="Number of similar cases needed to route confidently"
    )
    similarity_threshold: float = Field(
        default=0.75, description="Minimum similarity score for case matching"
    )

    # Voice Configuration
    sonic_model_id: str = Field(default="sonic-2", description="Cartesia TTS model ID")
    voice_id: str = Field(
        default="5c43e078-5ba4-4e1f-9639-8d85a403f76a", description="Cartesia voice ID"
    )

    # Data Storage Configuration
    data_dir: str = Field(
        default="siva_data", description="Directory for persistent data storage"
    )

    # OpenAI Configuration
    openai_model: str = Field(
        default="gpt-3.5-turbo-1106", description="OpenAI model for chat completions"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="OpenAI model for embeddings"
    )
    openai_whisper_model: str = Field(
        default="whisper-1", description="OpenAI model for speech-to-text"
    )
    openai_max_tokens: int = Field(
        default=300, description="Maximum tokens for OpenAI responses"
    )
    openai_temperature: float = Field(
        default=0.3, description="Temperature for OpenAI responses"
    )

    # Application Mode
    current_mode: str = Field(
        default="patient_intake",
        description="Current application mode: patient_intake or physician_consultation",
    )

    # CORS Configuration
    cors_origins: list[str] = Field(default=["*"], description="Allowed CORS origins")
    cors_credentials: bool = Field(default=True, description="Allow CORS credentials")
    cors_methods: list[str] = Field(default=["*"], description="Allowed CORS methods")
    cors_headers: list[str] = Field(default=["*"], description="Allowed CORS headers")

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra environment variables


# Global settings instance
settings = SivaSettings()
