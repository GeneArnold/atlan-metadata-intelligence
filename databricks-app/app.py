"""
Atlan Metadata Intelligence App - Phase 2
Simple interface to browse Atlan glossaries and terms via MCP.
"""

import streamlit as st
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

from config import Config
from atlan_client import AtlanClient

# Page configuration
st.set_page_config(
    page_title="Atlan Metadata Intelligence",
    page_icon="🔍",
    layout="wide"
)

# Title
st.title("🔍 Atlan Metadata Intelligence")
st.subheader("Browse Glossaries and Terms")

# Validate configuration
is_valid, error_msg = Config.validate()
if not is_valid:
    st.error(f"Configuration Error: {error_msg}")
    st.info("💡 Set ATLAN_API_KEY in your environment variables or .env file")
    st.stop()

# Initialize Atlan client
@st.cache_resource
def get_atlan_client():
    """Get or create Atlan client instance."""
    return AtlanClient(
        api_key=Config.ATLAN_API_KEY,
        atlan_host=Config.ATLAN_HOST
    )

client = get_atlan_client()

# Initialize session state
if 'glossaries' not in st.session_state:
    st.session_state.glossaries = []
if 'terms' not in st.session_state:
    st.session_state.terms = []
if 'selected_glossary' not in st.session_state:
    st.session_state.selected_glossary = None

# Layout: Two columns
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Glossaries")

    # Get Glossaries button
    if st.button("🔄 Get Glossaries", use_container_width=True):
        with st.spinner("Fetching glossaries from Atlan..."):
            try:
                # Get all glossaries
                glossaries = client.get_glossaries()

                st.session_state.glossaries = [
                    {
                        'name': g['displayName'],
                        'guid': g['guid'],
                        'description': g['description'],
                        'qualifiedName': g['qualifiedName']
                    }
                    for g in glossaries
                ]

                if st.session_state.glossaries:
                    st.success(f"✅ Found {len(st.session_state.glossaries)} glossaries")
                else:
                    st.warning("No glossaries found")

            except Exception as e:
                st.error(f"Error fetching glossaries: {str(e)}")
                st.session_state.glossaries = []

    # Glossary dropdown
    if st.session_state.glossaries:
        glossary_names = [g['name'] for g in st.session_state.glossaries]
        selected_name = st.selectbox(
            "Select a glossary:",
            options=glossary_names,
            key="glossary_select"
        )

        # Find the selected glossary details
        st.session_state.selected_glossary = next(
            (g for g in st.session_state.glossaries if g['name'] == selected_name),
            None
        )

        # Show glossary details
        if st.session_state.selected_glossary and st.session_state.selected_glossary.get('description'):
            st.info(f"📝 {st.session_state.selected_glossary['description']}")
    else:
        st.info("👆 Click 'Get Glossaries' to load glossaries from Atlan")

with col2:
    st.markdown("### Terms")

    # Get Terms button
    if st.button("🔄 Get Terms", use_container_width=True):
        if not st.session_state.selected_glossary:
            st.warning("⚠️ Please select a glossary first")
        else:
            with st.spinner(f"Fetching terms from {st.session_state.selected_glossary['name']}..."):
                try:
                    # Get terms for this glossary
                    glossary_qualified_name = st.session_state.selected_glossary['qualifiedName']

                    terms, debug_info = client.get_glossary_terms(glossary_qualified_name, debug=True)

                    # Debug: show what we got back
                    with st.expander("🔍 Debug Info - API Response Structure"):
                        st.write(f"**Querying glossary qualified name:** `{glossary_qualified_name}`")
                        st.write(f"**Query used:** {debug_info['query_used']}")
                        st.write(f"**Glossary qualified name:** {debug_info['glossary_qualified_name']}")

                    st.session_state.terms = [
                        {
                            'name': t['displayName'],
                            'guid': t['guid'],
                            'description': t['description']
                        }
                        for t in terms
                    ]

                    if st.session_state.terms:
                        st.success(f"✅ Found {len(st.session_state.terms)} terms")
                    else:
                        st.warning("No terms found in this glossary")

                except Exception as e:
                    st.error(f"Error fetching terms: {str(e)}")
                    st.exception(e)  # Show full stack trace
                    st.session_state.terms = []

    # Terms dropdown
    if st.session_state.terms:
        term_names = [t['name'] for t in st.session_state.terms]
        selected_term_name = st.selectbox(
            "Select a term:",
            options=term_names,
            key="term_select"
        )

        # Find the selected term details
        selected_term = next(
            (t for t in st.session_state.terms if t['name'] == selected_term_name),
            None
        )

        # Show term details
        if selected_term and selected_term.get('description'):
            st.info(f"📝 {selected_term['description']}")
    else:
        if st.session_state.selected_glossary:
            st.info("👆 Click 'Get Terms' to load terms from the selected glossary")
        else:
            st.info("Select a glossary first, then click 'Get Terms'")

# Divider
st.divider()

# Connection status in expander
with st.expander("ℹ️ Connection Info"):
    config_info = Config.get_info()
    for key, value in config_info.items():
        st.text(f"{key}: {value}")
