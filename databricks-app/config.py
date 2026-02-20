"""
Central configuration for Atlan Metadata Intelligence App.

This module manages all configuration including Atlan connection settings,
MCP server endpoints, and environment-specific settings.
"""

import os
from typing import Optional


class Config:
    """Application configuration."""

    # Atlan Configuration
    ATLAN_HOST: str = os.getenv("ATLAN_HOST", "https://partner-sandbox.atlan.com")
    ATLAN_API_KEY: str = os.getenv("ATLAN_API_KEY", "")

    # MCP Server Configuration
    # Using Atlan's hosted MCP endpoint
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "https://mcp.atlan.com/mcp")

    # App Settings
    APP_TITLE: str = "Atlan Metadata Intelligence"
    APP_ICON: str = "🔍"

    # MCP Tool Settings
    DEFAULT_SEARCH_LIMIT: int = 50
    MAX_LINEAGE_DEPTH: int = 3

    @classmethod
    def validate(cls) -> tuple[bool, Optional[str]]:
        """
        Validate that required configuration is present.

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cls.ATLAN_API_KEY:
            return False, "ATLAN_API_KEY is required. Set it in environment variables or .env file."

        if not cls.ATLAN_HOST:
            return False, "ATLAN_HOST is required."

        return True, None

    @classmethod
    def get_info(cls) -> dict:
        """
        Get configuration info for display (without sensitive data).

        Returns:
            Dictionary of configuration settings
        """
        return {
            "Atlan Host": cls.ATLAN_HOST,
            "MCP Server": cls.MCP_SERVER_URL,
            "API Key Status": "✓ Set" if cls.ATLAN_API_KEY else "✗ Not Set",
            "Search Limit": cls.DEFAULT_SEARCH_LIMIT,
            "Max Lineage Depth": cls.MAX_LINEAGE_DEPTH,
        }
