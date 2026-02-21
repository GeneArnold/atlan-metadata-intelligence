"""
Data Intelligence Assistant - Chat Interface
Natural language queries to Wide World Importers with PII protection.
"""

import streamlit as st
from dotenv import load_dotenv
import pandas as pd

# Load environment variables
load_dotenv()

from config import Config
from genie_client import GenieClient

# Page configuration
st.set_page_config(
    page_title="Data Intelligence Assistant",
    page_icon="💬",
    layout="wide"
)

# Custom CSS for chat styling
st.markdown("""
<style>
    /* Main title styling */
    .main-title {
        text-align: center;
        color: #888;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .genie-space {
        text-align: right;
        color: #666;
        font-size: 0.85rem;
        margin-bottom: 1.5rem;
        background-color: #2d3748;
        padding: 0.3rem 0.8rem;
        border-radius: 12px;
        display: inline-block;
        float: right;
    }

    /* Status indicators */
    .status-off {
        color: #ff4444;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }

    .status-on {
        color: #44ff44;
        font-size: 0.85rem;
        margin-bottom: 0.5rem;
    }

    /* Blocked message styling */
    .blocked-message {
        background: linear-gradient(135deg, #3d1a1a 0%, #2d1414 100%);
        border: 2px solid #ff4444;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .blocked-header {
        color: #ff6b6b;
        font-size: 1.1rem;
        font-weight: bold;
        margin-bottom: 1rem;
    }

    .blocked-content {
        color: #ddd;
        line-height: 1.6;
    }

    .blocked-field {
        margin: 0.5rem 0;
    }

    .blocked-label {
        color: #999;
        display: inline-block;
        width: 140px;
    }

    .blocked-value {
        color: #fff;
    }

    .classification-restricted {
        color: #ff4444;
        font-weight: bold;
    }

    .blocked-footer {
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #555;
        color: #aaa;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Check if Genie is configured
missing_config = []
if not Config.DATABRICKS_WORKSPACE_URL:
    missing_config.append("DATABRICKS_WORKSPACE_URL")
if not Config.DATABRICKS_TOKEN:
    missing_config.append("DATABRICKS_TOKEN")
if not Config.GENIE_SPACE_ID:
    missing_config.append("GENIE_SPACE_ID")

if missing_config:
    st.error(f"⚠️ Genie is not fully configured. Missing: {', '.join(missing_config)}")
    st.info("""
    **To configure Databricks Genie:**

    1. Set the following environment variables in your `.env` file:
       ```
       DATABRICKS_WORKSPACE_URL=https://your-workspace.cloud.databricks.com
       DATABRICKS_TOKEN=<your-databricks-token>
       GENIE_SPACE_ID=<your-genie-space-id>
       ```

    2. Restart the application
    """)
    st.stop()

# Initialize Genie client
@st.cache_resource
def get_genie_client():
    """Get or create Genie client instance."""
    return GenieClient(
        workspace_url=Config.DATABRICKS_WORKSPACE_URL,
        token=Config.DATABRICKS_TOKEN,
        space_id=Config.GENIE_SPACE_ID
    )

client = get_genie_client()

# Initialize session state
if 'chat_messages' not in st.session_state:
    st.session_state.chat_messages = []

if 'mcp_enabled' not in st.session_state:
    st.session_state.mcp_enabled = False

# Header
st.markdown('<div class="main-title">⚡ Powered by Databricks &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Wide World Importers — Data Intelligence Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="genie-space">Genie Space: WWI Sales</div>', unsafe_allow_html=True)
st.markdown('<div style="clear: both;"></div>', unsafe_allow_html=True)

# Display chat messages
for message in st.session_state.chat_messages:
    if message["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(message["content"])
    else:
        with st.chat_message("assistant", avatar="🤖"):
            # Status indicator with colored dot
            if message.get("mcp_enabled", False):
                st.markdown('<div class="status-on">🟢 Atlan MCP ON — Governance Active</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="status-off">🔴 Atlan MCP OFF — Unprotected</div>', unsafe_allow_html=True)

            # Check if this is a blocked message
            if message.get("blocked", False):
                # Display PII blocking message
                blocked_html = f"""
                <div class="blocked-message">
                    <div class="blocked-header">🚫 Access Blocked — PII Protected Asset</div>
                    <div class="blocked-content">
                        <p>The data you requested contains personally identifiable information (PII) and cannot be returned.</p>
                        <div class="blocked-field">
                            <span class="blocked-label">Asset:</span>
                            <span class="blocked-value">{message.get("blocked_asset", "wide_world_importers.processed_gold.dim_customer")}</span>
                        </div>
                        <div class="blocked-field">
                            <span class="blocked-label">Field:</span>
                            <span class="blocked-value">{message.get("blocked_field", "credit_limit")}</span>
                        </div>
                        <div class="blocked-field">
                            <span class="blocked-label">Classification:</span>
                            <span class="classification-restricted">PII — Restricted</span>
                        </div>
                        <div class="blocked-field">
                            <span class="blocked-label">Data Owner:</span>
                            <span class="blocked-value">Sarah Chen, Data Governance</span>
                        </div>
                        <div class="blocked-field">
                            <span class="blocked-label">Policy:</span>
                            <span class="blocked-value">GDPR Article 9 — Sensitive Personal Data</span>
                        </div>
                        <div class="blocked-field">
                            <span class="blocked-label">Request Access:</span>
                            <span class="blocked-value">sarah.chen@company.com</span>
                        </div>
                        <div class="blocked-footer">
                            💡 This asset is monitored by Atlan. Tag applied: <strong>PII — Restricted</strong> • Governance policy enforced via Atlan MCP.
                        </div>
                    </div>
                </div>
                """
                st.markdown(blocked_html, unsafe_allow_html=True)
            else:
                # Normal message display
                st.markdown(message["content"])

                # SQL query in expander (if available)
                if message.get("sql_query"):
                    with st.expander("📝 View SQL Query"):
                        st.code(message["sql_query"], language="sql")

                # Results table (if available)
                if message.get("results_df") is not None:
                    st.dataframe(message["results_df"], use_container_width=True)
                    st.caption(f"📊 {len(message['results_df'])} rows returned")

# Controls row - RIGHT ABOVE chat input
col1, col2 = st.columns([6, 1])

with col1:
    subcol1, subcol2 = st.columns([1, 4])
    with subcol1:
        mcp_enabled = st.toggle(
            "Atlan MCP:",
            value=st.session_state.mcp_enabled,
            help="When ON, queries containing PII keywords are blocked with governance message"
        )
        if mcp_enabled != st.session_state.mcp_enabled:
            st.session_state.mcp_enabled = mcp_enabled
            st.rerun()

    with subcol2:
        if st.session_state.mcp_enabled:
            st.markdown('<div style="color: #44ff44; font-size: 1rem; padding-top: 0.3rem; font-weight: bold;">🟢 ON — Governance Active</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color: #ff4444; font-size: 1rem; padding-top: 0.3rem; font-weight: bold;">🔴 OFF — Unprotected</div>', unsafe_allow_html=True)

with col2:
    if st.button("🗑️ Clear", use_container_width=True):
        st.session_state.chat_messages = []
        st.rerun()

# Chat input
user_input = st.chat_input('Try: "Show me customers with credit limits over $3,000" or "What are the top selling products?"')

if user_input:
    # Add user message to chat
    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input
    })

    # Display user message immediately
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)

    # Process with Genie or block if MCP is ON
    with st.chat_message("assistant", avatar="🤖"):
        # Show status
        if st.session_state.mcp_enabled:
            st.markdown('<div class="status-on">🟢 Atlan MCP ON — Governance Active</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-off">🔴 Atlan MCP OFF — Unprotected</div>', unsafe_allow_html=True)

        # Check for PII-related keywords if MCP is enabled (simple demo logic)
        pii_keywords = ["credit", "credit limit", "credit card", "phone", "address", "contact", "personal"]
        should_block = st.session_state.mcp_enabled and any(keyword in user_input.lower() for keyword in pii_keywords)

        # Prepare assistant message
        assistant_message = {
            "role": "assistant",
            "mcp_enabled": st.session_state.mcp_enabled
        }

        if should_block:
            # Block the query and show PII protection message
            assistant_message["blocked"] = True
            assistant_message["blocked_asset"] = "wide_world_importers.processed_gold.dim_customer"

            # Determine which field based on keywords
            if "credit" in user_input.lower():
                assistant_message["blocked_field"] = "credit_limit"
            elif "phone" in user_input.lower():
                assistant_message["blocked_field"] = "phone_number"
            elif "address" in user_input.lower():
                assistant_message["blocked_field"] = "delivery_address_line_1"
            else:
                assistant_message["blocked_field"] = "credit_limit"

            assistant_message["content"] = "Access blocked due to PII protection."

            # Display blocking message
            blocked_html = f"""
            <div class="blocked-message">
                <div class="blocked-header">🚫 Access Blocked — PII Protected Asset</div>
                <div class="blocked-content">
                    <p>The data you requested contains personally identifiable information (PII) and cannot be returned.</p>
                    <div class="blocked-field">
                        <span class="blocked-label">Asset:</span>
                        <span class="blocked-value">{assistant_message["blocked_asset"]}</span>
                    </div>
                    <div class="blocked-field">
                        <span class="blocked-label">Field:</span>
                        <span class="blocked-value">{assistant_message["blocked_field"]}</span>
                    </div>
                    <div class="blocked-field">
                        <span class="blocked-label">Classification:</span>
                        <span class="classification-restricted">PII — Restricted</span>
                    </div>
                    <div class="blocked-field">
                        <span class="blocked-label">Data Owner:</span>
                        <span class="blocked-value">Sarah Chen, Data Governance</span>
                    </div>
                    <div class="blocked-field">
                        <span class="blocked-label">Policy:</span>
                        <span class="blocked-value">GDPR Article 9 — Sensitive Personal Data</span>
                    </div>
                    <div class="blocked-field">
                        <span class="blocked-label">Request Access:</span>
                        <span class="blocked-value">sarah.chen@company.com</span>
                    </div>
                    <div class="blocked-footer">
                        💡 This asset is monitored by Atlan. Tag applied: <strong>PII — Restricted</strong> • Governance policy enforced via Atlan MCP.
                    </div>
                </div>
            </div>
            """
            st.markdown(blocked_html, unsafe_allow_html=True)

        else:
            # Process normally with Genie
            with st.spinner("Processing your question..."):
                result = client.ask_question(user_input, max_wait_seconds=300)

            if result["status"] == "completed":
                # Build response text
                response_text = result.get("text_response", "Here are the results:")
                assistant_message["content"] = response_text

                # Display response
                st.markdown(response_text)

                # Add SQL query if available
                if result.get("sql_query"):
                    assistant_message["sql_query"] = result["sql_query"]
                    with st.expander("📝 View SQL Query"):
                        st.code(result["sql_query"], language="sql")

                # Process and display results
                if result.get("query_results"):
                    try:
                        query_data = result["query_results"]

                        if "statement_response" in query_data:
                            stmt_response = query_data["statement_response"]

                            if "result" in stmt_response and "data_array" in stmt_response["result"]:
                                data_array = stmt_response["result"]["data_array"]

                                # Get column names
                                if "manifest" in stmt_response and "schema" in stmt_response["manifest"]:
                                    columns = [col["name"] for col in stmt_response["manifest"]["schema"]["columns"]]
                                else:
                                    columns = [f"Column_{i}" for i in range(len(data_array[0]) if data_array else 0)]

                                # Create DataFrame
                                if data_array:
                                    df = pd.DataFrame(data_array, columns=columns)
                                    assistant_message["results_df"] = df

                                    st.dataframe(df, use_container_width=True)
                                    st.caption(f"📊 {len(df)} rows returned")
                                else:
                                    st.info("Query executed successfully but returned no rows.")
                    except Exception as e:
                        st.error(f"Error displaying results: {str(e)}")

            elif result["status"] == "failed":
                assistant_message["content"] = f"❌ Query failed: {result.get('error', 'Unknown error')}"
                st.error(assistant_message["content"])

            elif result["status"] == "timeout":
                assistant_message["content"] = f"⏱️ Query timed out after waiting. Please try again."
                st.warning(assistant_message["content"])

            else:
                assistant_message["content"] = f"❌ An error occurred: {result.get('error', 'Unknown status')}"
                st.error(assistant_message["content"])

        # Add assistant message to chat history
        st.session_state.chat_messages.append(assistant_message)
