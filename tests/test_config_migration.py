"""
Test configuration migration from old config/settings.py to new src/siva/settings.py
"""

import sys
from pathlib import Path
import os
from unittest.mock import patch

# Add src directory to Python path for absolute imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest

from siva.settings import settings, get_siva_config, get_tau2_config


class TestConfigurationMigration:
    """Test that the new configuration system works correctly."""

    def test_new_settings_loaded(self):
        """Test that new settings are properly loaded."""
        assert settings is not None
        assert hasattr(settings, "openai_api_key")
        assert hasattr(settings, "app_host")
        assert hasattr(settings, "data_dir")

    def test_tau2_config_compatibility(self):
        """Test that tau2-bench configuration is properly generated."""
        tau2_config = get_tau2_config()

        # Check required tau2-bench fields
        assert "max_steps" in tau2_config
        assert "max_errors" in tau2_config
        assert "seed" in tau2_config
        assert "agent_llm" in tau2_config
        assert "user_llm" in tau2_config

        # Check values are reasonable
        assert tau2_config["max_steps"] > 0
        assert tau2_config["max_errors"] > 0
        assert isinstance(tau2_config["agent_llm"], str)
        assert isinstance(tau2_config["user_llm"], str)

    def test_siva_config_compatibility(self):
        """Test that SIVA-specific configuration is properly generated."""
        siva_config = get_siva_config()

        # Check required SIVA fields
        assert "openai_api_key" in siva_config
        assert "app_host" in siva_config
        assert "app_port" in siva_config
        assert "data_dir" in siva_config
        assert "current_mode" in siva_config

        # Check values are reasonable
        assert isinstance(siva_config["app_host"], str)
        assert isinstance(siva_config["app_port"], int)
        assert siva_config["app_port"] > 0
        assert isinstance(siva_config["data_dir"], str)

    def test_environment_variable_loading(self):
        """Test that environment variables are properly loaded."""
        # Test with mock environment variables
        with patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "test-key-123",
                "CARTESIA_API_KEY": "test-cartesia-key",
                "APP_HOST": "test-host",
                "APP_PORT": "9000",
                "DATA_DIR": "test-data-dir",
            },
        ):
            # Recreate settings with new environment
            from siva.settings import SivaSettings

            test_settings = SivaSettings()

            assert test_settings.openai_api_key == "test-key-123"
            assert test_settings.cartesia_api_key == "test-cartesia-key"
            assert test_settings.app_host == "test-host"
            assert test_settings.app_port == 9000
            assert test_settings.data_dir == "test-data-dir"

    def test_default_values(self):
        """Test that default values are properly set."""
        # Test some key default values
        assert settings.app_host == "localhost"
        assert settings.app_port == 8000
        assert settings.data_dir == "siva_data"
        assert settings.current_mode == "patient_intake"
        assert settings.retrieval_threshold == 3
        assert settings.similarity_threshold == 0.75

    def test_configuration_types(self):
        """Test that configuration values have correct types."""
        assert isinstance(settings.app_host, str)
        assert isinstance(settings.app_port, int)
        assert isinstance(settings.app_reload, bool)
        assert isinstance(settings.app_debug, bool)
        assert isinstance(settings.retrieval_threshold, int)
        assert isinstance(settings.similarity_threshold, float)
        assert isinstance(settings.cors_origins, list)
        assert isinstance(settings.cors_methods, list)
        assert isinstance(settings.cors_headers, list)

    def test_backward_compatibility_structure(self):
        """Test that the new settings maintain the same structure as the old ones."""
        # Check that all old settings fields are available in new settings
        old_fields = [
            "openai_api_key",
            "cartesia_api_key",
            "app_host",
            "app_port",
            "app_reload",
            "app_debug",
            "client_host",
            "client_port",
            "retrieval_threshold",
            "similarity_threshold",
            "sonic_model_id",
            "voice_id",
            "data_dir",
            "openai_model",
            "openai_embedding_model",
            "openai_whisper_model",
            "openai_max_tokens",
            "openai_temperature",
            "current_mode",
            "cors_origins",
            "cors_credentials",
            "cors_methods",
            "cors_headers",
        ]

        for field in old_fields:
            assert hasattr(settings, field), f"Missing field: {field}"


if __name__ == "__main__":
    pytest.main([__file__])
