"""
Governance Testing Page
Simple page to test Atlan MCP PII tag detection.
"""

import streamlit as st
from dotenv import load_dotenv
import asyncio
import json
from datetime import datetime

# Load environment variables
load_dotenv()

from config import Config
from atlan_mcp_client import AtlanMCPClient, run_async

# Log file path
LOG_FILE = "/Users/gene.arnold/WorkSpace/atlan-databricks-mdlh-app/pii_test_log.json"

# Page configuration
st.set_page_config(
    page_title="Governance Testing",
    page_icon="🧪"
)

st.title("🧪 PII Detection Test")
st.caption("Simple POC - Check if query columns have PII tags")

# Check if Atlan is configured
if not Config.MCP_SERVER_URL or not Config.ATLAN_API_KEY:
    st.error("⚠️ Atlan MCP is not configured.")
    st.stop()

# Initialize Atlan client
@st.cache_resource
def get_atlan_client():
    return AtlanMCPClient(
        mcp_server_url=Config.MCP_SERVER_URL,
        api_key=Config.ATLAN_API_KEY
    )

client = get_atlan_client()

# Sample SQL (what Genie returns)
st.subheader("1. Sample Query")
sample_sql = """SELECT customer_name, credit_limit
FROM dim_customer
WHERE credit_limit > 3000"""

st.code(sample_sql, language="sql")

# Columns in the query
st.subheader("2. Columns to Check")
columns_to_check = ["CustomerName", "CreditLimit"]
st.write(", ".join([f"`{col}`" for col in columns_to_check]))

st.divider()

# PII Check
st.subheader("3. Check Atlan for PII Tags")

if st.button("Run All Tests", use_container_width=True, type="primary"):
    st.subheader("4. Test Results")

    # Test different queries
    test_queries = [
        "Find Databricks columns (fields) in Atlan that are marked as PII, including any columns tagged or classified as PII.",
        "Find Databricks columns in dim_customer marked as PII",
        "columns with PII tag in dim_customer",
        "CustomerName CreditLimit PII",
        "dim_customer PII"
    ]

    # Log structure
    test_log = {
        "timestamp": datetime.now().isoformat(),
        "tests": []
    }

    for i, query in enumerate(test_queries, 1):
        st.write(f"**Test {i}:** `{query[:60]}...`" if len(query) > 60 else f"**Test {i}:** `{query}`")

        test_result = {
            "test_number": i,
            "query": query,
            "status": "unknown",
            "pii_columns_found": [],
            "total_assets": 0,
            "error": None,
            "sample_asset": None
        }

        try:
            result = run_async(client.semantic_search(query=query, limit=50))

            # DEBUG: Log response type and structure
            st.write(f"  → Response type: {type(result)}")
            st.write(f"  → Response value: {str(result)[:200]}")

            # Check if it's a list (like FastMCP might return)
            if isinstance(result, list):
                st.write(f"  → IT'S A LIST with {len(result)} items")
                if len(result) > 0:
                    st.write(f"  → First item type: {type(result[0])}")
                    # Try to extract from first item
                    if isinstance(result[0], dict):
                        result = result[0]  # Unwrap
                        st.write(f"  → Unwrapped first dict, keys: {list(result.keys())}")

            # DEBUG: Save raw result
            test_result["raw_response"] = str(result)[:1000]  # Truncate for log size

            # Count results
            if isinstance(result, dict):
                st.write(f"  → Dict keys: {list(result.keys())}")
                total_assets = len(result.get("assets", []))
            else:
                st.error(f"  → Unexpected result type: {type(result)}")
                total_assets = 0

            test_result["total_assets"] = total_assets
            st.write(f"  → Total assets: {total_assets}")

            # Find PII columns
            pii_columns = []
            if "assets" in result:
                for asset in result["assets"]:
                    if 'atlan_tags' in asset:
                        has_pii = any(tag.get('type_name') == 'PII' for tag in asset['atlan_tags'])
                        if has_pii:
                            column_name = asset.get('name', 'Unknown').replace('NAME: ', '')
                            pii_columns.append(column_name)

            test_result["pii_columns_found"] = pii_columns

            # Display
            if pii_columns:
                test_result["status"] = "success"
                st.success(f"✅ Found {len(pii_columns)} PII columns: {', '.join(pii_columns)}")
            else:
                test_result["status"] = "no_pii_found"
                st.warning(f"❌ No PII found ({total_assets} assets returned)")

            # Save sample asset
            if total_assets > 0:
                test_result["sample_asset"] = result["assets"][0]
                with st.expander(f"Show first asset from Test {i}"):
                    st.json(result["assets"][0])

        except Exception as e:
            test_result["status"] = "error"
            test_result["error"] = str(e)
            st.error(f"Error: {str(e)}")

        test_log["tests"].append(test_result)
        st.divider()

    # Write log file
    try:
        with open(LOG_FILE, 'w') as f:
            json.dump(test_log, f, indent=2)
        st.success(f"📝 Test results logged to: {LOG_FILE}")
    except Exception as e:
        st.error(f"Failed to write log: {str(e)}")

st.divider()

# View log file
if st.button("📖 View Last Test Log"):
    try:
        with open(LOG_FILE, 'r') as f:
            log_data = json.load(f)

        st.subheader("Test Log Summary")
        st.write(f"**Timestamp:** {log_data.get('timestamp', 'N/A')}")

        for test in log_data.get('tests', []):
            status_emoji = "✅" if test['status'] == 'success' else "❌" if test['status'] == 'error' else "⚠️"
            st.write(f"{status_emoji} **Test {test['test_number']}**: {test['status']}")
            st.write(f"  - Query: `{test['query'][:60]}...`" if len(test['query']) > 60 else f"  - Query: `{test['query']}`")
            st.write(f"  - PII columns found: {test['pii_columns_found']}")
            st.write(f"  - Total assets: {test['total_assets']}")
            if test['error']:
                st.write(f"  - Error: {test['error']}")

        with st.expander("Full Log JSON"):
            st.json(log_data)

    except FileNotFoundError:
        st.warning("No log file found. Run tests first.")
    except Exception as e:
        st.error(f"Error reading log: {str(e)}")
