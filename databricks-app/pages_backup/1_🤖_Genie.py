"""
Databricks Genie Space Interface
Query the Wide World Importers data warehouse using natural language via Genie API.
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
    page_title="Genie - Atlan Metadata Intelligence",
    page_icon="🤖",
    layout="wide"
)

# Title
st.title("🤖 Databricks Genie Space")
st.subheader("Natural Language Data Queries")

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

    2. **To find your Genie Space ID:**
       - Go to your Genie space in Databricks
       - Click on the Settings tab
       - Copy the Space ID

    3. Restart the application
    """)
    st.stop()

st.success(f"✅ Connected to Genie Space: `{Config.GENIE_SPACE_ID}`")

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

# Initialize session state for conversation history
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Example questions
with st.expander("💡 Example Questions"):
    st.markdown("""
    Try asking questions like:
    - "Show me the top 10 customers by total orders"
    - "What are the most popular stock items?"
    - "Show employee sales performance"
    - "What's the average order value by customer category?"
    - "How many orders were placed last month?"
    """)

# Query interface
st.markdown("---")
st.markdown("### Ask Genie")

question = st.text_area(
    "Enter your natural language query:",
    placeholder="e.g., Show me total orders by customer type",
    height=100,
    key="genie_question"
)

col1, col2 = st.columns([1, 4])
with col1:
    ask_button = st.button("🚀 Ask Genie", use_container_width=True, type="primary")

if ask_button and question:
    with st.spinner(f"🔍 Genie is processing your question..."):
        # Ask the question
        result = client.ask_question(question, max_wait_seconds=300)

        # Add to conversation history
        st.session_state.conversation_history.append({
            "question": question,
            "result": result
        })

        # Display result
        if result["status"] == "completed":
            st.success("✅ Query completed!")

            # Show text response
            if result["text_response"]:
                st.markdown("#### Genie's Response")
                st.info(result["text_response"])

            # Show generated SQL
            if result["sql_query"]:
                with st.expander("📝 Generated SQL"):
                    st.code(result["sql_query"], language="sql")

            # Show query results
            if result["query_results"]:
                st.markdown("#### Query Results")

                try:
                    query_data = result["query_results"]

                    # Check if we have statement_response with result data
                    if "statement_response" in query_data:
                        stmt_response = query_data["statement_response"]

                        if "result" in stmt_response and "data_array" in stmt_response["result"]:
                            # Extract column names and data
                            data_array = stmt_response["result"]["data_array"]

                            # Get column names from manifest
                            if "manifest" in stmt_response and "schema" in stmt_response["manifest"]:
                                columns = [col["name"] for col in stmt_response["manifest"]["schema"]["columns"]]
                            else:
                                # Fallback: use generic column names
                                columns = [f"Column_{i}" for i in range(len(data_array[0]) if data_array else 0)]

                            # Create DataFrame
                            if data_array:
                                df = pd.DataFrame(data_array, columns=columns)
                                st.dataframe(df, use_container_width=True)

                                # Show row count
                                st.caption(f"📊 {len(df)} rows returned")
                            else:
                                st.info("Query executed successfully but returned no rows.")
                        else:
                            st.warning("Query results format not recognized")
                            with st.expander("Raw query results"):
                                st.json(query_data)
                    else:
                        st.warning("No statement_response found in query results")
                        with st.expander("Raw query results"):
                            st.json(query_data)

                except Exception as e:
                    st.error(f"Error displaying results: {str(e)}")
                    with st.expander("Raw query results"):
                        st.json(result["query_results"])

        elif result["status"] == "failed":
            st.error(f"❌ Query failed: {result['error']}")
        elif result["status"] == "timeout":
            st.warning(f"⏱️ Query timed out: {result['error']}")
        else:
            st.error(f"❌ Unknown error: {result.get('error', 'Unknown status')}")

elif ask_button and not question:
    st.warning("⚠️ Please enter a question")

# Conversation history
if st.session_state.conversation_history:
    st.markdown("---")
    st.markdown("### Conversation History")

    for idx, item in enumerate(reversed(st.session_state.conversation_history)):
        with st.expander(f"Q: {item['question'][:100]}{'...' if len(item['question']) > 100 else ''}"):
            result = item['result']

            st.markdown(f"**Question:** {item['question']}")

            if result["status"] == "completed":
                if result["text_response"]:
                    st.markdown(f"**Answer:** {result['text_response']}")

                if result["sql_query"]:
                    st.code(result["sql_query"], language="sql")
            else:
                st.error(f"Status: {result['status']}, Error: {result.get('error', 'N/A')}")

    # Clear history button
    if st.button("🗑️ Clear History"):
        st.session_state.conversation_history = []
        st.rerun()

# Connection info
with st.expander("ℹ️ Configuration"):
    st.text(f"Workspace URL: {Config.DATABRICKS_WORKSPACE_URL}")
    st.text(f"Space ID: {Config.GENIE_SPACE_ID}")
    st.text(f"Token: {'✓ Set' if Config.DATABRICKS_TOKEN else '✗ Not Set'}")
