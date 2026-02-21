"""
Data Intelligence Assistant - Clean Chat Interface
Based on Streamlit's chatbot example with Atlan MCP integration.
"""

import streamlit as st
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

from config import Config
from genie_client import GenieClient
from governance import GovernanceEngine, init_governance_engine, refresh_pii_cache

# Page configuration
st.set_page_config(
    page_title="Data Intelligence Assistant",
    page_icon="💬"
)

# Initialize session state FIRST (before sidebar uses it)
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if "mcp_enabled" not in st.session_state:
    st.session_state.mcp_enabled = False

if "genie_conversation_id" not in st.session_state:
    st.session_state.genie_conversation_id = None

# Initialize governance engine
if "governance_engine" not in st.session_state and Config.ATLAN_API_KEY:
    st.session_state.governance_engine = init_governance_engine(
        atlan_host=Config.ATLAN_HOST,
        atlan_api_key=Config.ATLAN_API_KEY
    )

# Sidebar controls
with st.sidebar:
    st.title("⚙️ Controls")

    # Atlan Protection Toggle
    mcp_enabled = st.toggle(
        "Atlan Protection",
        value=st.session_state.get("mcp_enabled", False),
        help="When ON, queries are checked against Atlan governance policies before execution"
    )

    # Update session state if toggle changed
    if mcp_enabled != st.session_state.get("mcp_enabled", False):
        st.session_state.mcp_enabled = mcp_enabled

    # Status indicator
    if st.session_state.get("mcp_enabled", False):
        st.success("🟢 ON — Governance Active")
    else:
        st.error("🔴 OFF — Unprotected")

    st.divider()

    # Clear chat button
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.chat_messages = []
        st.session_state.genie_conversation_id = None  # Start fresh conversation
        st.rerun()

    st.divider()

    # Conversation status
    if st.session_state.get("genie_conversation_id"):
        st.caption(f"💬 **Active conversation**")
        st.caption(f"ID: `{st.session_state.genie_conversation_id[:16]}...`")
    else:
        st.caption("💬 **No active conversation**")

    st.divider()

    # Refresh policies button (hidden implementation detail)
    if st.session_state.get("governance_engine"):
        engine = st.session_state.governance_engine

        # Refresh button - no cache terminology
        if st.button("🔄 Sync Atlan Policies", use_container_width=True):
            count, error = refresh_pii_cache(engine)
            if error:
                st.error(f"❌ Sync failed")
            else:
                st.success(f"✅ Policies synced")
            st.rerun()

    st.divider()

    # Connection info
    st.caption("**Genie Space:** WWI Sales")
    st.caption(f"**Workspace:** {Config.DATABRICKS_WORKSPACE_URL[:30]}...")

# Check if Genie is configured
missing_config = []
if not Config.DATABRICKS_WORKSPACE_URL:
    missing_config.append("DATABRICKS_WORKSPACE_URL")
if not Config.DATABRICKS_TOKEN:
    missing_config.append("DATABRICKS_TOKEN")
if not Config.GENIE_SPACE_ID:
    missing_config.append("GENIE_SPACE_ID")

if missing_config:
    st.error(f"⚠️ Genie is not configured. Missing: {', '.join(missing_config)}")
    st.stop()

# Initialize Genie client
@st.cache_resource
def get_genie_client():
    return GenieClient(
        workspace_url=Config.DATABRICKS_WORKSPACE_URL,
        token=Config.DATABRICKS_TOKEN,
        space_id=Config.GENIE_SPACE_ID
    )

client = get_genie_client()

# Main title
st.title("💬 Data Intelligence Assistant")
st.caption("⚡ Powered by Databricks • Wide World Importers")

# Display chat messages
for msg in st.session_state.chat_messages:
    if msg["role"] == "user":
        st.chat_message("user").write(msg["content"])
    else:
        with st.chat_message("assistant"):
            # Status indicator
            if msg.get("mcp_enabled", False):
                st.caption("🟢 Atlan Protection ON — Governance Active")
            else:
                st.caption("🔴 Atlan Protection OFF — Unprotected")

            # Check if blocked
            if msg.get("blocked", False):
                st.error(f"🚫 **Access Blocked — PII Protected Asset**")

                # Show blocked columns if available
                blocked_cols = msg.get("blocked_columns", [])
                if blocked_cols:
                    st.markdown(f"""
                    The data you requested contains personally identifiable information (PII) and cannot be returned.

                    **Blocked Columns ({len(blocked_cols)}):**
                    """)
                    for col in blocked_cols:
                        st.markdown(f"- `{col}` - PII")
                else:
                    st.markdown("""
                    The data you requested contains personally identifiable information (PII) and cannot be returned.
                    """)

                st.markdown("""
                **Policy:** GDPR Article 9 — Sensitive Personal Data
                **Data Owner:** Data Governance Team
                **Request Access:** governance@company.com

                💡 *This asset is monitored by Atlan. Governance policy enforced via Atlan Python SDK.*
                """)
            else:
                # Normal response
                st.write(msg["content"])

                # SQL query
                if msg.get("sql_query"):
                    with st.expander("📝 View SQL Query"):
                        st.code(msg["sql_query"], language="sql")

                # Results table
                if msg.get("results_df") is not None:
                    st.dataframe(msg["results_df"], use_container_width=True)
                    st.caption(f"📊 {len(msg['results_df'])} rows returned")

# Chat input
if prompt := st.chat_input("Try: 'Show me customers with credit limits over $3,000' or 'What are the top selling products?'"):
    # Add user message
    st.session_state.chat_messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Process with Genie - 2-STEP FLOW
    with st.chat_message("assistant"):
        st.caption("🔴 Atlan Protection OFF — Unprotected" if not st.session_state.mcp_enabled else "🟢 Atlan Protection ON — Governance Active")

        with st.spinner("🔍 Analyzing your question... checking data catalog..."):
            # STEP 1: Generate SQL ONLY (don't execute yet)
            result = client.generate_sql_only(
                prompt,
                conversation_id=st.session_state.genie_conversation_id,
                max_wait_seconds=300
            )

            # Store conversation_id for next message
            if result.get("conversation_id"):
                st.session_state.genie_conversation_id = result["conversation_id"]

        if result["status"] == "completed":
            # SQL was generated successfully
            response_text = result.get("text_response", "Here are the results:")
            sql_query = result.get("sql_query")

            # STEP 2: Check if protection is enabled
            if st.session_state.mcp_enabled and st.session_state.get("governance_engine"):
                # Protection is ON - run real Atlan governance check
                engine = st.session_state.governance_engine
                governance_result = engine.check_query(sql_query)

                if governance_result["blocked"]:
                    # PII detected - BLOCK
                    st.error(f"🚫 **Access Blocked — PII Protected Asset**")

                    # Show which columns triggered the block
                    blocked_cols = governance_result["blocked_columns"]
                    col_details = governance_result["column_details"]

                    st.markdown(f"""
                    The data you requested contains personally identifiable information (PII) and cannot be returned.

                    **Blocked Columns ({len(blocked_cols)}):**
                    """)

                    for col in blocked_cols:
                        details = col_details.get(col, {})
                        st.markdown(f"- `{col}` - {', '.join(details.get('classifications', ['PII']))}")

                    st.markdown(f"""
                    **Policy:** GDPR Article 9 — Sensitive Personal Data
                    **Data Owner:** Data Governance Team
                    **Request Access:** governance@company.com

                    💡 *This asset is monitored by Atlan. Governance policy enforced in real-time.*
                    """)

                    # Store message (blocked)
                    assistant_msg = {
                        "role": "assistant",
                        "mcp_enabled": True,
                        "blocked": True,
                        "blocked_columns": blocked_cols,
                        "content": f"Query blocked: {len(blocked_cols)} PII column(s) detected",
                        "sql_query": sql_query,
                        "results_df": None
                    }
                    st.session_state.chat_messages.append(assistant_msg)

                else:
                    # No PII - execute the query normally (no special message)
                    with st.spinner("Executing query..."):
                        exec_result = client.execute_query(
                            conversation_id=result["conversation_id"],
                            message_id=result["message_id"],
                            attachment_id=result["attachment_id"]
                        )

                    if exec_result["status"] == "completed":
                        st.write(response_text)

                        # Store message
                        assistant_msg = {
                            "role": "assistant",
                            "mcp_enabled": True,
                            "blocked": False,
                            "content": response_text,
                            "sql_query": sql_query,
                            "results_df": None
                        }

                        # SQL query
                        if sql_query:
                            with st.expander("📝 View SQL Query"):
                                st.code(sql_query, language="sql")

                        # Results
                        if exec_result.get("query_results"):
                            try:
                                query_data = exec_result["query_results"]
                                if "statement_response" in query_data:
                                    stmt_response = query_data["statement_response"]
                                    if "result" in stmt_response and "data_array" in stmt_response["result"]:
                                        data_array = stmt_response["result"]["data_array"]

                                        if "manifest" in stmt_response and "schema" in stmt_response["manifest"]:
                                            columns = [col["name"] for col in stmt_response["manifest"]["schema"]["columns"]]
                                        else:
                                            columns = [f"Column_{i}" for i in range(len(data_array[0]) if data_array else 0)]

                                        if data_array:
                                            import pandas as pd
                                            df = pd.DataFrame(data_array, columns=columns)
                                            assistant_msg["results_df"] = df
                                            st.dataframe(df, use_container_width=True)
                                            st.caption(f"📊 {len(df)} rows returned")
                            except Exception as e:
                                st.error(f"Error displaying results: {str(e)}")

                        st.session_state.chat_messages.append(assistant_msg)

                    else:
                        # Execution failed
                        error_msg = f"❌ Query execution failed: {exec_result.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "mcp_enabled": True,
                            "blocked": False,
                            "content": error_msg
                        })

            else:
                # Protection is OFF - execute the query
                # Check if we have attachment_id
                if not result.get("attachment_id"):
                    st.error("❌ No query attachment found. The SQL may not have generated properly.")
                    st.session_state.chat_messages.append({
                        "role": "assistant",
                        "mcp_enabled": False,
                        "content": "Error: No query attachment found"
                    })
                else:
                    with st.spinner("Executing query..."):
                        # Execute the query using the attachment_id
                        exec_result = client.execute_query(
                            conversation_id=result["conversation_id"],
                            message_id=result["message_id"],
                            attachment_id=result["attachment_id"]
                        )

                    # Check if execution succeeded
                    if exec_result["status"] == "completed":
                        st.write(response_text)

                        # Store message
                        assistant_msg = {
                            "role": "assistant",
                            "mcp_enabled": False,
                            "content": response_text,
                            "sql_query": sql_query,
                            "results_df": None
                        }

                        # SQL query
                        if sql_query:
                            with st.expander("📝 View SQL Query"):
                                st.code(sql_query, language="sql")

                        # Results
                        if exec_result.get("query_results"):
                            try:
                                query_data = exec_result["query_results"]
                                if "statement_response" in query_data:
                                    stmt_response = query_data["statement_response"]
                                    if "result" in stmt_response and "data_array" in stmt_response["result"]:
                                        data_array = stmt_response["result"]["data_array"]

                                        if "manifest" in stmt_response and "schema" in stmt_response["manifest"]:
                                            columns = [col["name"] for col in stmt_response["manifest"]["schema"]["columns"]]
                                        else:
                                            columns = [f"Column_{i}" for i in range(len(data_array[0]) if data_array else 0)]

                                        if data_array:
                                            df = pd.DataFrame(data_array, columns=columns)
                                            assistant_msg["results_df"] = df
                                            st.dataframe(df, use_container_width=True)
                                            st.caption(f"📊 {len(df)} rows returned")
                            except Exception as e:
                                st.error(f"Error displaying results: {str(e)}")

                        st.session_state.chat_messages.append(assistant_msg)

                    else:
                        # Execution failed
                        error_msg = f"❌ Query execution failed: {exec_result.get('error', 'Unknown error')}"
                        st.error(error_msg)
                        st.session_state.chat_messages.append({
                            "role": "assistant",
                            "mcp_enabled": False,
                            "content": error_msg
                        })

        elif result["status"] == "failed":
            error_msg = f"❌ SQL generation failed: {result.get('error', 'Unknown error')}"
            st.error(error_msg)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "mcp_enabled": st.session_state.mcp_enabled,
                "content": error_msg
            })
        else:
            error_msg = f"⏱️ Query timed out or encountered an error"
            st.warning(error_msg)
            st.session_state.chat_messages.append({
                "role": "assistant",
                "mcp_enabled": st.session_state.mcp_enabled,
                "content": error_msg
            })
