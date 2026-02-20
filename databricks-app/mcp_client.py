"""
Atlan MCP (Model Context Protocol) Client.

This module provides a Python wrapper for calling Atlan's MCP server tools.
The MCP server exposes Atlan metadata through four core tools:
- search_assets: Search for assets by name, type, tags, etc.
- get_assets_by_dsl: Query assets using Atlan's DSL
- traverse_lineage: Walk upstream/downstream lineage
- update_assets: Update asset descriptions, certification, etc.
"""

import httpx
from typing import Optional, Dict, List, Any
import json


class AtlanMCPClient:
    """Client for interacting with Atlan MCP Server."""

    def __init__(self, api_key: str, atlan_host: str, mcp_server_url: str):
        """
        Initialize the Atlan MCP client.

        Args:
            api_key: Atlan API key (JWT token)
            atlan_host: Atlan workspace URL (e.g., https://your-org.atlan.com)
            mcp_server_url: MCP server endpoint
        """
        self.api_key = api_key
        self.atlan_host = atlan_host
        self.mcp_server_url = mcp_server_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool with the given parameters.

        Args:
            tool_name: Name of the MCP tool to call
            parameters: Tool parameters

        Returns:
            Tool response as dictionary

        Raises:
            httpx.HTTPError: If the request fails
        """
        payload = {
            "tool": tool_name,
            "parameters": parameters,
            "atlan_host": self.atlan_host,
        }

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                self.mcp_server_url,
                json=payload,
                headers=self.headers,
            )
            response.raise_for_status()
            return response.json()

    def search_assets(
        self,
        query: str,
        asset_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        domain: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Search for assets in Atlan.

        Args:
            query: Search query string (searches name, description, etc.)
            asset_type: Filter by asset type (e.g., "Table", "Column", "Dashboard")
            tags: Filter by tags
            domain: Filter by domain
            limit: Maximum number of results to return

        Returns:
            Dictionary containing:
            - assets: List of matching assets
            - total: Total number of matches
            - query: The query that was executed

        Example:
            >>> client.search_assets("customer", asset_type="Table", limit=10)
        """
        parameters = {
            "query": query,
            "limit": limit,
        }

        if asset_type:
            parameters["asset_type"] = asset_type
        if tags:
            parameters["tags"] = tags
        if domain:
            parameters["domain"] = domain

        return self._call_tool("search_assets", parameters)

    def get_assets_by_dsl(self, dsl_query: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve assets using Atlan's DSL query language.

        This is more powerful than search_assets for complex queries.

        Args:
            dsl_query: Atlan DSL query dictionary

        Returns:
            Dictionary containing matching assets

        Example:
            >>> dsl = {
            ...     "query": {
            ...         "bool": {
            ...             "must": [
            ...                 {"term": {"__typeName.keyword": "Table"}},
            ...                 {"term": {"certificateStatus": "VERIFIED"}}
            ...             ]
            ...         }
            ...     }
            ... }
            >>> client.get_assets_by_dsl(dsl)
        """
        parameters = {"dsl_query": dsl_query}
        return self._call_tool("get_assets_by_dsl", parameters)

    def traverse_lineage(
        self,
        asset_guid: str,
        direction: str = "downstream",
        depth: int = 3,
    ) -> Dict[str, Any]:
        """
        Traverse lineage for an asset.

        Args:
            asset_guid: GUID of the asset to start from
            direction: "upstream" or "downstream"
            depth: How many levels deep to traverse (default: 3)

        Returns:
            Dictionary containing:
            - root_asset: The starting asset
            - lineage: List of connected assets
            - relationships: List of relationships between assets

        Example:
            >>> client.traverse_lineage("abc-123-def", direction="upstream", depth=2)
        """
        parameters = {
            "asset_guid": asset_guid,
            "direction": direction,
            "depth": depth,
        }
        return self._call_tool("traverse_lineage", parameters)

    def update_asset(
        self,
        asset_guid: str,
        description: Optional[str] = None,
        user_description: Optional[str] = None,
        certificate_status: Optional[str] = None,
        certificate_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an asset's metadata.

        Args:
            asset_guid: GUID of the asset to update
            description: System description (usually auto-generated)
            user_description: User-provided description
            certificate_status: Certification status (VERIFIED, DRAFT, DEPRECATED)
            certificate_message: Certification message/reason

        Returns:
            Dictionary containing the updated asset

        Example:
            >>> client.update_asset(
            ...     "abc-123",
            ...     user_description="Customer data table",
            ...     certificate_status="VERIFIED"
            ... )
        """
        parameters = {"asset_guid": asset_guid}

        if description is not None:
            parameters["description"] = description
        if user_description is not None:
            parameters["user_description"] = user_description
        if certificate_status is not None:
            parameters["certificate_status"] = certificate_status
        if certificate_message is not None:
            parameters["certificate_message"] = certificate_message

        return self._call_tool("update_asset", parameters)

    def test_connection(self) -> tuple[bool, str]:
        """
        Test the connection to Atlan MCP server.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Try a simple search with limit 1
            result = self.search_assets("", limit=1)
            return True, "Successfully connected to Atlan MCP server"
        except httpx.HTTPError as e:
            return False, f"Connection failed: {str(e)}"
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"
