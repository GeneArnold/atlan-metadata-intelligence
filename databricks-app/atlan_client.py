"""
Atlan REST API Client.

This module provides a Python wrapper for calling Atlan's REST API.
"""

import httpx
from typing import Optional, Dict, List, Any
import json


class AtlanClient:
    """Client for interacting with Atlan REST API."""

    def __init__(self, api_key: str, atlan_host: str):
        """
        Initialize the Atlan client.

        Args:
            api_key: Atlan API key (JWT token)
            atlan_host: Atlan workspace URL (e.g., https://your-org.atlan.com)
        """
        self.api_key = api_key
        self.atlan_host = atlan_host.rstrip("/")
        self.api_base = f"{self.atlan_host}/api/meta"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def search(
        self,
        type_name: str,
        query: str = "*",
        limit: int = 50,
        offset: int = 0,
        attributes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Search for assets in Atlan using DSL.

        Args:
            type_name: Asset type (e.g., "AtlasGlossary", "AtlasGlossaryTerm")
            query: Search query (default: "*" for all)
            limit: Maximum number of results
            offset: Offset for pagination
            attributes: List of attributes to retrieve

        Returns:
            Dictionary containing search results
        """
        # Build Elasticsearch DSL query
        dsl = {
            "from": offset,
            "size": limit,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"__typeName.keyword": type_name}},
                        {"term": {"__state": "ACTIVE"}}
                    ]
                }
            }
        }

        # Add query string if not wildcard
        if query and query != "*":
            dsl["query"]["bool"]["must"].append({
                "query_string": {
                    "query": f"*{query}*",
                    "fields": ["name^5", "displayName^5", "description", "userDescription"]
                }
            })

        # Add attributes filter if specified
        if attributes:
            dsl["_source"] = attributes

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/search/indexsearch",
                    json={"dsl": dsl},
                    headers=self.headers,
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            raise Exception(f"Atlan API error: {str(e)}")

    def get_glossaries(self) -> List[Dict[str, Any]]:
        """
        Get all glossaries from Atlan.

        Returns:
            List of glossary dictionaries
        """
        result = self.search(type_name="AtlasGlossary", limit=100)

        if not result or "entities" not in result:
            return []

        glossaries = []
        for entity in result.get("entities", []):
            attrs = entity.get("attributes", {})
            glossaries.append({
                "guid": entity.get("guid"),
                "name": attrs.get("name", "Unnamed"),
                "displayName": attrs.get("displayName") or attrs.get("name", "Unnamed"),
                "description": attrs.get("userDescription") or attrs.get("description", ""),
                "qualifiedName": attrs.get("qualifiedName", ""),
            })

        return glossaries

    def get_glossary_terms(self, glossary_qualified_name: str, debug: bool = False) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Get all terms for a specific glossary.

        Args:
            glossary_qualified_name: Qualified name of the glossary
            debug: If True, return debug info as second element of tuple

        Returns:
            Tuple of (list of term dictionaries, debug info dict)
        """
        debug_info = {
            "query_used": "",
            "glossary_qualified_name": glossary_qualified_name,
        }

        # Build DSL query to search for terms in this glossary
        # Key insight: __glossary field contains the qualified_name, not the GUID!
        dsl = {
            "from": 0,
            "size": 500,
            "query": {
                "bool": {
                    "must": [
                        {"term": {"__typeName.keyword": "AtlasGlossaryTerm"}},
                        {"term": {"__state": "ACTIVE"}},
                        {"term": {"__glossary": glossary_qualified_name}}  # Use qualified_name!
                    ]
                }
            }
        }

        debug_info["query_used"] = str(dsl)

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/search/indexsearch",
                    json={"dsl": dsl},
                    headers=self.headers,
                )
                response.raise_for_status()
                result = response.json()

                if not result or "entities" not in result:
                    return [], debug_info

                terms = []
                for entity in result.get("entities", []):
                    attrs = entity.get("attributes", {})
                    terms.append({
                        "guid": entity.get("guid"),
                        "name": attrs.get("name", "Unnamed"),
                        "displayName": attrs.get("displayName") or attrs.get("name", "Unnamed"),
                        "description": attrs.get("userDescription") or attrs.get("description", ""),
                        "qualifiedName": attrs.get("qualifiedName", ""),
                    })

                return terms, debug_info

        except httpx.HTTPError as e:
            raise Exception(f"Atlan API error: {str(e)}")

    def test_connection(self) -> tuple[bool, str]:
        """
        Test the connection to Atlan.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Try to get glossaries
            self.get_glossaries()
            return True, "Successfully connected to Atlan"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"
