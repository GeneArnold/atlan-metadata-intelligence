# Architecture & Governance Design
**Last Updated:** 2026-02-20
**Status:** Design Phase - Ready for Implementation

---

## Executive Summary

This document describes the governance-first architecture for the Atlan Metadata Intelligence App, which integrates **Databricks Genie** (natural language to SQL) with **Atlan MCP** (metadata governance) to enforce PII protection policies before data is accessed.

**Key Discovery:** Genie API separates SQL generation from execution, enabling true pre-query governance checks.

---

## Architecture Overview

### The Governance Challenge

**Problem:** Traditional BI tools execute queries immediately when generated. By the time governance rules are checked, sensitive data has already been retrieved from the database.

**Solution:** Intercept the SQL between generation and execution, validate against Atlan's metadata governance policies, then conditionally execute only if approved.

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (Streamlit)               │
│  - Natural language query input                             │
│  - Atlan MCP ON/OFF toggle (sidebar)                        │
│  - Chat history display                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Databricks Genie Conversation API              │
│  Step 1: POST /start-conversation → Returns conversation_id│
│  Step 2: Poll /messages/{message_id} → Get COMPLETED status│
│  Step 3: Extract SQL from attachments (NO EXECUTION YET)   │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   SQL Parser & Analyzer                     │
│  - Extract table.column references from generated SQL       │
│  - Map to Atlan asset qualified names                       │
│  - Build governance check request                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  Atlan MCP Governance Check                 │
│  IF MCP ENABLED:                                            │
│    - Call search_assets for each table.column reference     │
│    - Check for PII classification tags                      │
│    - Retrieve data owner, policy info                       │
│  IF MCP DISABLED:                                           │
│    - Skip governance check                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
            ┌─────────┴──────────┐
            │                    │
            ▼                    ▼
    ┌──────────────┐    ┌──────────────────┐
    │ PII DETECTED │    │   SAFE TO RUN    │
    │   🚫 BLOCK   │    │   ✅ EXECUTE     │
    └──────┬───────┘    └────────┬─────────┘
           │                     │
           ▼                     ▼
  ┌────────────────┐   ┌──────────────────────────┐
  │ Return blocked │   │ Call Genie result API    │
  │ message with   │   │ GET /query-result/       │
  │ governance     │   │   {attachment_id}        │
  │ details        │   │ Return data to user      │
  └────────────────┘   └──────────────────────────┘
```

---

## Genie API Workflow - Critical Discovery

### The Game-Changer: Separation of Generation and Execution

**Documentation confirms:** Genie API does NOT automatically execute queries when they are generated.

#### Workflow Steps:

1. **Start Conversation**
   ```
   POST /api/2.0/genie/spaces/{space_id}/start-conversation
   Body: { "content": "Show me customers with credit limits over $3,000" }
   Response: { "conversation_id": "...", "message_id": "..." }
   ```

2. **Poll for SQL Generation**
   ```
   GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}

   Response when status = "COMPLETED":
   {
     "status": "COMPLETED",
     "attachments": [
       {
         "query": {
           "query": "SELECT * FROM dim_customer WHERE credit_limit > 3000",
           "description": "...",
           "statement_id": "..."
         },
         "attachment_id": "abc123"  ← KEY: Used to fetch results separately
       }
     ]
   }
   ```

3. **Conditional Execution** (Only if governance check passes)
   ```
   GET /api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}

   Returns: Actual query results
   ```

**Key Insight:** Step 3 is a SEPARATE API call. We can intercept after Step 2, check Atlan, and only call Step 3 if approved.

---

## Atlan MCP Integration

### Atlan MCP Server Endpoints

**Base URL:** `https://partner-sandbox.atlan.com/mcp/api-key`

**Authentication:** API Key in headers

**Primary Tool:** `search_assets`

### Governance Check Logic

```python
def check_pii_governance(sql_query: str) -> dict:
    """
    Parse SQL and check Atlan for PII tags.

    Returns:
        {
            "blocked": bool,
            "reason": str,
            "asset": str,
            "field": str,
            "classification": str,
            "owner": str,
            "policy": str
        }
    """
    # Step 1: Parse SQL to extract table.column references
    columns = parse_sql_columns(sql_query)
    # Example: ["dim_customer.credit_limit", "dim_customer.customer_name"]

    # Step 2: For each column, search in Atlan
    for col in columns:
        table, field = col.split(".")

        # Build Atlan qualified name
        qualified_name = f"wide_world_importers.processed_gold.{table}"

        # Call Atlan MCP search_assets
        result = atlan_client.search_assets(
            qualified_name=qualified_name,
            attributes=["classifications", "ownerUsers", "certificateStatus"]
        )

        # Check if field has PII classification
        if field in result.get("classifications", {}).get("PII", []):
            return {
                "blocked": True,
                "reason": "PII Protected Asset",
                "asset": qualified_name,
                "field": field,
                "classification": "PII — Restricted",
                "owner": result.get("ownerUsers", [{}])[0].get("name", "Unknown"),
                "policy": "GDPR Article 9 — Sensitive Personal Data"
            }

    return {"blocked": False}
```

---

## Current Implementation Status

### What's Built (as of 2026-02-20)

✅ **Page 1:** Atlan Glossaries Browser (`app.py`)
- MCP client connects to Atlan
- Browse glossaries and terms
- Semantic search

✅ **Page 2:** Genie Example (`pages/1_🤖_Genie.py`)
- Basic Genie Conversation API integration
- Displays SQL and results
- No governance layer

✅ **Page 3:** Clean Chat Interface (`pages/3_💬_Chat.py`) ← **NEW**
- Based on Streamlit chatbot example
- Sidebar controls (Atlan MCP toggle, Clear button)
- Centered chat layout (no `layout="wide"`)
- **Simple keyword-based blocking** (temporary governance)
- Full Genie integration with SQL display and results tables

✅ **Genie Client:** (`genie_client.py`)
- `ask_question()` method
- Handles polling, SQL extraction, result retrieval
- **Currently executes in one call** - needs refactoring for governance

✅ **Atlan MCP Client:** (`atlan_mcp_client.py`)
- `get_glossaries()`, `get_glossary_terms()`, `semantic_search()`
- **Needs:** `search_assets()` for governance checks

### What Needs to Be Built

🔲 **Refactor Genie Client** - Separate generation from execution
- New method: `generate_sql_only(question)` → Returns SQL without executing
- New method: `execute_sql(attachment_id)` → Executes pre-approved SQL
- Update `ask_question()` to use 2-step flow when governance is enabled

🔲 **SQL Parser Module** (`sql_parser.py`)
- Extract table.column references from SQL
- Map to Atlan qualified names
- Handle JOINs, subqueries, aliases

🔲 **Governance Engine** (`governance.py`)
- `check_governance(sql: str, mcp_enabled: bool)` → Governance decision
- Integrate Atlan MCP `search_assets` calls
- Cache governance decisions for performance

🔲 **Atlan MCP Enhancements**
- Add `search_assets()` method for asset lookup
- Add `get_column_classifications()` helper
- Add `get_data_owner()` helper

🔲 **UI Updates**
- Display governance blocking message with full details
- Show "Checking governance..." spinner
- Add governance decision to message metadata

🔲 **Configuration**
- Asset mapping config (`genie_assets.py`) - Map Genie tables to Atlan qualified names
- PII field definitions - Which columns are known PII

---

## Genie Space Instructions

**Discovery:** Genie spaces have an "Instructions" tab that acts as a system prompt.

**Location:** Configure → Instructions tab

**Potential Uses:**
1. **Self-documentation:** "Always list the full qualified names (schema.table.column) of all columns in your SQL query in the text response."
2. **Business context:** "The credit_limit field contains sensitive financial data."
3. **Query style:** "Always use explicit JOINs. Never use SELECT *."

**Status:** Not yet configured - available for optimization

---

## File Structure

```
atlan-databricks-mdlh-app/
├── databricks-app/
│   ├── app.py                          # Page 1: Atlan Glossaries
│   ├── pages/
│   │   ├── 1_🤖_Genie.py              # Page 2: Genie Example
│   │   ├── 2_💬_Chatbot.py            # OLD - DO NOT USE
│   │   └── 3_💬_Chat.py               # Page 3: NEW Clean Chat (ACTIVE)
│   ├── config.py                       # Configuration
│   ├── genie_client.py                 # Genie Conversation API client
│   └── atlan_mcp_client.py             # Atlan MCP client
│
├── ARCHITECTURE_GOVERNANCE.md          # This document
├── PROJECT_STATUS.md                   # Current project status
├── GENIE_INTEGRATION_NOTES.md          # Genie technical notes
├── CLAUDE.md                           # Instructions for Claude Code
├── project-handoff.md                  # Original requirements
└── README.md                           # User-facing overview
```

---

## Layout & UI Lessons Learned

### The Positioning Struggle (Solved)

**Problem:** Trying to position toggle/clear controls above chat input led to complex CSS, fixed positioning conflicts, and broken layouts.

**Solution:** Move controls to **sidebar**. Streamlit's sidebar is designed for this.

**Key Learnings:**
1. ❌ **Don't use** `layout="wide"` for chat interfaces - ruins centered chat width
2. ❌ **Don't use** fixed positioning - conflicts with `st.chat_input()`
3. ❌ **Don't use** `st.container(height=X)` - creates unwanted scrollboxes
4. ✅ **Do use** sidebar for persistent controls
5. ✅ **Do use** Streamlit's default centered layout for chat
6. ✅ **Do follow** official Streamlit chatbot example structure

### Streamlit Chatbot Pattern (Reference)

Source: https://github.com/streamlit/llm-examples/blob/main/Chatbot.py

**Simple structure:**
```python
# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display message history
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat input (automatically positioned at bottom)
if prompt := st.chat_input():
    # Append user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    # Get response
    response = get_ai_response(prompt)

    # Append and display assistant message
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
```

**No containers, no positioning tricks, no layout hacks - just works.**

---

## Next Steps (Priority Order)

### Phase 1: Governance Infrastructure (Week 1)
1. **Refactor `genie_client.py`** to separate generation from execution
2. **Build `sql_parser.py`** for extracting table.column references
3. **Enhance `atlan_mcp_client.py`** with `search_assets()` method
4. **Create `governance.py`** engine with decision logic
5. **Update Chat page** to use new 2-step flow

### Phase 2: Asset Mapping & Configuration (Week 1)
6. **Create `genie_assets.py`** config mapping
7. **Tag PII fields in Atlan** (credit_limit, phone_number, etc.)
8. **Test governance flow** with safe and blocked queries
9. **Add caching** for governance decisions

### Phase 3: UI Polish & Error Handling (Week 2)
10. **Enhanced blocking messages** with full governance details
11. **Loading states** - "Generating SQL...", "Checking governance..."
12. **Error handling** - Failed governance checks, Atlan unavailable
13. **Governance audit log** in session state

### Phase 4: Optimization & Production (Week 2-3)
14. **Configure Genie Instructions** for better SQL self-documentation
15. **Performance testing** with complex queries
16. **Deploy to Databricks Apps**
17. **Documentation for users** (README, demo script)

---

## Success Criteria

✅ **Governance Works:**
- Query with PII field → Blocked before execution
- Query with safe fields → Returns data
- Toggle OFF → All queries execute (for demo)

✅ **User Experience:**
- Natural language input works
- Clear visual feedback on governance state
- Blocking messages are informative, not just "access denied"

✅ **Technical:**
- No false positives (safe queries blocked)
- No false negatives (PII queries allowed)
- Response time < 5 seconds for governance + query

---

## References

- **Genie Conversation API Docs:** https://docs.databricks.com/aws/en/genie/conversation-api
- **Atlan MCP Server:** https://partner-sandbox.atlan.com/mcp/api-key
- **Streamlit Chatbot Example:** https://github.com/streamlit/llm-examples/blob/main/Chatbot.py
- **Wide World Importers Dataset:** `wide_world_importers.processed_gold` (Databricks Unity Catalog)

---

**End of Document**
