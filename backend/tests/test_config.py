"""
Unit tests for application configuration.
"""

import pytest
from app.core.config import Settings, get_settings


class TestSettings:
    """Tests for the Settings configuration class."""

    def test_default_mongodb_uri(self):
        """Test that default MongoDB URI is set correctly."""
        # Arrange & Act
        settings = Settings()

        # Assert
        assert settings.MONGODB_URI == "mongodb://localhost:27017"

    def test_default_database_name(self):
        """Test that default database name is set correctly."""
        # Arrange & Act
        settings = Settings()

        # Assert
        assert settings.DATABASE_NAME == "fleet_management"

    def test_default_pagination_limits(self):
        """Test that default pagination limits are set correctly."""
        # Arrange & Act
        settings = Settings()

        # Assert
        assert settings.DEFAULT_PAGE_LIMIT == 50
        assert settings.MAX_PAGE_LIMIT == 500

    def test_cors_origins_list_parses_comma_separated(self):
        """Test that CORS origins string is correctly parsed into a list."""
        # Arrange
        settings = Settings(CORS_ORIGINS="http://localhost:3000,http://localhost:8080")

        # Act
        origins = settings.cors_origins_list

        # Assert
        assert origins == ["http://localhost:3000", "http://localhost:8080"]

    def test_cors_origins_list_trims_whitespace(self):
        """Test that CORS origins list trims whitespace from entries."""
        # Arrange
        settings = Settings(
            CORS_ORIGINS="http://localhost:3000 , http://localhost:8080 "
        )

        # Act
        origins = settings.cors_origins_list

        # Assert
        assert origins == ["http://localhost:3000", "http://localhost:8080"]

    def test_get_settings_returns_settings_instance(self):
        """Test that get_settings returns a Settings instance."""
        # Arrange & Act
        settings = get_settings()

        # Assert
        assert isinstance(settings, Settings)

    def test_get_settings_is_cached(self):
        """Test that get_settings returns the same cached instance."""
        # Arrange & Act
        settings1 = get_settings()
        settings2 = get_settings()

        # Assert
        assert settings1 is settings2
