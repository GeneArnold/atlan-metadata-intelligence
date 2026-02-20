import streamlit as st
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Databricks + Streamlit Test",
    page_icon="🚀",
    layout="wide"
)

# Title
st.title("Databricks + Streamlit: Workflow Test")

# Success banner
st.success("Connected to Databricks Apps ✓")

# Show current timestamp to prove it's live
st.subheader("Current Timestamp")
st.write(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Interactive input
st.subheader("Echo Test")
user_input = st.text_input("Enter some text:")

if st.button("Echo"):
    if user_input:
        st.info(f"You said: {user_input}")
    else:
        st.warning("Please enter some text first!")

# Status info
st.divider()
st.caption("This is a Phase 1 test app to validate the local → Git → Databricks workflow.")
