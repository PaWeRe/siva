"""
SIVA Settings Module - Bridge between old and new configuration systems.
This provides backward compatibility while migrating to tau2-bench architecture.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from . import config


class SivaSettings(BaseSettings):
    """SIVA application settings using Pydantic BaseSettings with tau2-bench compatibility."""

    # API Keys
    openai_api_key: str = Field(..., description="OpenAI API key for chat and STT")
    cartesia_api_key: str = Field(..., description="Cartesia API key for TTS")

    # FastAPI Configuration
    app_host: str = Field(default=config.APP_HOST, description="FastAPI host")
    app_port: int = Field(default=config.APP_PORT, description="FastAPI port")
    app_reload: bool = Field(
        default=config.APP_RELOAD, description="FastAPI auto-reload"
    )
    app_debug: bool = Field(default=config.APP_DEBUG, description="Debug mode")

    # Client Server Configuration
    client_host: str = Field(
        default=config.CLIENT_HOST, description="Client server host"
    )
    client_port: int = Field(
        default=config.CLIENT_PORT, description="Client server port"
    )

    # Vector Store Configuration
    retrieval_threshold: int = Field(
        default=config.RETRIEVAL_THRESHOLD,
        description="Number of similar cases needed to route confidently",
    )
    similarity_threshold: float = Field(
        default=config.SIMILARITY_THRESHOLD,
        description="Minimum similarity score for case matching",
    )

    # Voice Configuration
    sonic_model_id: str = Field(
        default=config.SONIC_MODEL_ID, description="Cartesia TTS model ID"
    )
    voice_id: str = Field(default=config.VOICE_ID, description="Cartesia voice ID")

    # Data Storage Configuration
    data_dir: str = Field(
        default=config.DATA_DIR, description="Directory for persistent data storage"
    )

    # OpenAI Configuration
    openai_model: str = Field(
        default=config.OPENAI_MODEL, description="OpenAI model for chat completions"
    )
    openai_embedding_model: str = Field(
        default=config.OPENAI_EMBEDDING_MODEL, description="OpenAI model for embeddings"
    )
    openai_whisper_model: str = Field(
        default=config.OPENAI_WHISPER_MODEL,
        description="OpenAI model for speech-to-text",
    )
    openai_max_tokens: int = Field(
        default=config.OPENAI_MAX_TOKENS,
        description="Maximum tokens for OpenAI responses",
    )
    openai_temperature: float = Field(
        default=config.OPENAI_TEMPERATURE,
        description="Temperature for OpenAI responses",
    )

    # Application Mode
    current_mode: str = Field(
        default=config.CURRENT_MODE,
        description="Current application mode: patient_intake or physician_consultation",
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=config.CORS_ORIGINS, description="Allowed CORS origins"
    )
    cors_credentials: bool = Field(
        default=config.CORS_CREDENTIALS, description="Allow CORS credentials"
    )
    cors_methods: list[str] = Field(
        default=config.CORS_METHODS, description="Allowed CORS methods"
    )
    cors_headers: list[str] = Field(
        default=config.CORS_HEADERS, description="Allowed CORS headers"
    )

    # Tau2-bench Configuration
    max_steps: int = Field(
        default=config.DEFAULT_MAX_STEPS, description="Maximum simulation steps"
    )
    max_errors: int = Field(
        default=config.DEFAULT_MAX_ERRORS, description="Maximum errors before stopping"
    )
    seed: int = Field(
        default=config.DEFAULT_SEED, description="Random seed for reproducibility"
    )
    max_concurrency: int = Field(
        default=config.DEFAULT_MAX_CONCURRENCY,
        description="Maximum concurrent simulations",
    )
    num_trials: int = Field(
        default=config.DEFAULT_NUM_TRIALS, description="Number of trials per task"
    )
    log_level: str = Field(
        default=config.DEFAULT_LOG_LEVEL, description="Logging level"
    )

    # LLM Configuration
    agent_llm: str = Field(
        default=config.DEFAULT_LLM_AGENT, description="LLM for agent"
    )
    user_llm: str = Field(
        default=config.DEFAULT_LLM_USER, description="LLM for user simulator"
    )
    agent_temperature: float = Field(
        default=config.DEFAULT_LLM_TEMPERATURE_AGENT,
        description="Agent LLM temperature",
    )
    user_temperature: float = Field(
        default=config.DEFAULT_LLM_TEMPERATURE_USER, description="User LLM temperature"
    )

    class Config:
        """Pydantic configuration."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra environment variables


# Global settings instance
settings = SivaSettings()


def get_tau2_config() -> dict:
    """Get tau2-bench compatible configuration dictionary."""
    return {
        "max_steps": settings.max_steps,
        "max_errors": settings.max_errors,
        "seed": settings.seed,
        "max_concurrency": settings.max_concurrency,
        "num_trials": settings.num_trials,
        "log_level": settings.log_level,
        "agent_llm": settings.agent_llm,
        "user_llm": settings.user_llm,
        "agent_temperature": settings.agent_temperature,
        "user_temperature": settings.user_temperature,
        "llm_cache_enabled": config.LLM_CACHE_ENABLED,
        "redis_host": config.REDIS_HOST,
        "redis_port": config.REDIS_PORT,
        "redis_password": config.REDIS_PASSWORD,
        "redis_prefix": config.REDIS_PREFIX,
        "use_langfuse": config.USE_LANGFUSE,
    }


def get_siva_config() -> dict:
    """Get SIVA-specific configuration dictionary."""
    return {
        "openai_api_key": settings.openai_api_key,
        "cartesia_api_key": settings.cartesia_api_key,
        "app_host": settings.app_host,
        "app_port": settings.app_port,
        "app_reload": settings.app_reload,
        "app_debug": settings.app_debug,
        "client_host": settings.client_host,
        "client_port": settings.client_port,
        "retrieval_threshold": settings.retrieval_threshold,
        "similarity_threshold": settings.similarity_threshold,
        "sonic_model_id": settings.sonic_model_id,
        "voice_id": settings.voice_id,
        "data_dir": settings.data_dir,
        "openai_model": settings.openai_model,
        "openai_embedding_model": settings.openai_embedding_model,
        "openai_whisper_model": settings.openai_whisper_model,
        "openai_max_tokens": settings.openai_max_tokens,
        "openai_temperature": settings.openai_temperature,
        "current_mode": settings.current_mode,
        "cors_origins": settings.cors_origins,
        "cors_credentials": settings.cors_credentials,
        "cors_methods": settings.cors_methods,
        "cors_headers": settings.cors_headers,
    }
