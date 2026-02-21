"""
Atlan Governance Module - PII Protection Layer

This module provides real-time governance checks for SQL queries by:
1. Building a PII cache from Atlan metadata (via REST API)
2. Parsing SQL to extract column references
3. Checking if any columns have PII classifications in Atlan

Architecture: Cached + Refresh (Option 3)
- Fast: In-memory lookups
- Demo-friendly: Refresh button updates from Atlan
- Accurate: Real Atlan data, not hardcoded
"""

from typing import Dict, List, Tuple, Optional
from sql_metadata import Parser
import httpx
import streamlit as st


class GovernanceEngine:
    """
    Governance engine that checks SQL queries against Atlan PII policies.
    """

    def __init__(self, atlan_host: str, atlan_api_key: str):
        """
        Initialize governance engine with Atlan connection.

        Args:
            atlan_host: Atlan workspace URL (e.g., https://partner-sandbox.atlan.com)
            atlan_api_key: Atlan API key
        """
        self.atlan_host = atlan_host.rstrip("/")
        self.atlan_api_key = atlan_api_key
        self.api_base = f"{self.atlan_host}/api/meta"
        self.headers = {
            "Authorization": f"Bearer {atlan_api_key}",
            "Content-Type": "application/json",
        }

        # PII cache: {table.column: classification_info}
        self.pii_cache: Dict[str, Dict] = {}

        # Classification GUID to name mapping
        self.classification_map = self._load_classification_mappings()

    def _load_classification_mappings(self) -> Dict[str, str]:
        """Load classification GUID to display name mapping."""
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.api_base}/types/typedefs",
                    headers=self.headers,
                )
                response.raise_for_status()
                result = response.json()

                # Build GUID -> DisplayName map
                mapping = {}
                for classif in result.get('classificationDefs', []):
                    guid = classif.get('name')  # In Atlan, 'name' is the GUID
                    display_name = classif.get('displayName', guid)
                    mapping[guid] = display_name

                return mapping
        except Exception as e:
            print(f"Warning: Could not load classification mappings: {e}")
            return {}

    def build_pii_cache(self) -> Tuple[Dict[str, Dict], int, Optional[str]]:
        """
        Query Atlan for all columns with PII tags using REST API.

        Returns:
            Tuple of (cache_dict, columns_found, error_message)
        """
        cache = {}
        total_columns = 0
        error = None

        try:
            # Search for all Column assets in processed_gold schema
            dsl = {
                "from": 0,
                "size": 1000,
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"__typeName.keyword": "Column"}},
                            {"term": {"__state": "ACTIVE"}},
                            {"wildcard": {"qualifiedName": "*processed_gold*"}}
                        ]
                    }
                }
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_base}/search/indexsearch",
                    json={"dsl": dsl},
                    headers=self.headers,
                )
                response.raise_for_status()
                result = response.json()

            # Process results
            if "entities" in result:
                for entity in result["entities"]:
                    # Check for PII classification
                    classifications = entity.get("classifications", [])

                    # Check if ANY classification maps to "PII"
                    pii_classifs = []
                    for c in classifications:
                        type_name = c.get("typeName", "")
                        display_name = self.classification_map.get(type_name, type_name)
                        if display_name == "PII":
                            pii_classifs.append(display_name)

                    if pii_classifs:
                        # Extract column name from attributes
                        attrs = entity.get("attributes", {})
                        column_name = attrs.get("name")
                        qualified_name = attrs.get("qualifiedName", "")

                        # Extract table name from qualifiedName
                        # Format: default/databricks/.../database/schema/table/column
                        table_name = None
                        if qualified_name:
                            parts = qualified_name.split("/")
                            if len(parts) >= 2:
                                table_name = parts[-2]  # Second to last part is table name

                        if column_name and table_name:
                            # Build cache key: table.column
                            cache_key = f"{table_name}.{column_name}"

                            cache[cache_key] = {
                                "column": column_name,
                                "table": table_name,
                                "qualified_name": qualified_name,
                                "classifications": pii_classifs,
                                "description": attrs.get("userDescription", "No description")
                            }

                            total_columns += 1

            self.pii_cache = cache

        except Exception as e:
            error = f"Error building PII cache: {str(e)}"

        return cache, total_columns, error

    def check_query(self, sql: str) -> Dict:
        """
        Check if SQL query accesses PII-protected columns.

        Args:
            sql: SQL query string

        Returns:
            Dictionary with:
                - blocked: bool
                - blocked_columns: List[str] (columns that triggered block)
                - column_details: Dict (detailed info about blocked columns)
                - sql: str (original SQL)
                - message: str (human-readable message)
        """
        try:
            # Parse SQL to extract column references
            parser = Parser(sql)
            select_columns = parser.columns_dict.get('select', [])

            # Check each SELECT column against PII cache
            blocked_columns = []
            column_details = {}

            for col in select_columns:
                # sql-metadata returns: "table.column" or just "column"
                # Check both formats
                if col in self.pii_cache:
                    blocked_columns.append(col)
                    column_details[col] = self.pii_cache[col]
                else:
                    # Try without table prefix (for SELECT without table alias)
                    for cached_key in self.pii_cache.keys():
                        if cached_key.endswith(f".{col}"):
                            blocked_columns.append(cached_key)
                            column_details[cached_key] = self.pii_cache[cached_key]
                            break

            # Build result
            if blocked_columns:
                return {
                    "blocked": True,
                    "blocked_columns": blocked_columns,
                    "column_details": column_details,
                    "sql": sql,
                    "message": f"Query blocked: {len(blocked_columns)} PII-protected column(s) detected"
                }
            else:
                return {
                    "blocked": False,
                    "blocked_columns": [],
                    "column_details": {},
                    "sql": sql,
                    "message": "Query approved: No PII columns detected"
                }

        except Exception as e:
            # If parsing fails, be safe and block
            return {
                "blocked": True,
                "blocked_columns": [],
                "column_details": {},
                "sql": sql,
                "message": f"Query blocked: Error parsing SQL - {str(e)}"
            }

    def get_cache_status(self) -> Dict:
        """
        Get current status of PII cache.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "total_pii_columns": len(self.pii_cache),
            "cached_columns": list(self.pii_cache.keys()),
            "tables_covered": list(set(info['table'] for info in self.pii_cache.values()))
        }


# Streamlit session state helpers
def init_governance_engine(atlan_host: str, atlan_api_key: str) -> GovernanceEngine:
    """
    Initialize governance engine and load PII policies from Atlan.

    Args:
        atlan_host: Atlan workspace URL
        atlan_api_key: Atlan API key

    Returns:
        GovernanceEngine instance
    """
    engine = GovernanceEngine(atlan_host, atlan_api_key)

    # Load PII policies from Atlan
    cache, count, error = engine.build_pii_cache()

    if error:
        # Silent fail - just log to console, don't show warning to user
        print(f"Warning: Could not load PII policies from Atlan: {error}")

    return engine


def refresh_pii_cache(engine: GovernanceEngine) -> Tuple[int, Optional[str]]:
    """
    Refresh PII cache from Atlan (for demo button).

    Args:
        engine: GovernanceEngine instance

    Returns:
        Tuple of (columns_found, error_message)
    """
    cache, count, error = engine.build_pii_cache()

    return count, error
