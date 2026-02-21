# Databricks Genie Integration - Technical Notes

## Overview
Successfully integrated Databricks Genie Conversation API to allow natural language querying of the Wide World Importers data warehouse.

**🎯 CRITICAL DISCOVERY (2026-02-20):** Genie API separates SQL generation from execution, enabling governance checks before data is accessed. See "SQL Generation vs Execution" section below.

## Key Files
- `databricks-app/genie_client.py` - Genie API client wrapper
- `databricks-app/pages/1_🤖_Genie.py` - Streamlit UI for Genie
- `databricks-app/config.py` - Configuration (credentials)

## Configuration Required
```bash
# In .env file
DATABRICKS_WORKSPACE_URL=https://dbc-8d941db8-48cd.cloud.databricks.com
DATABRICKS_TOKEN=<your-databricks-token>
GENIE_SPACE_ID=01f10ea33fc010dcb2dc604b75ac4336
```

## API Workflow
1. **Start Conversation**: POST to `/api/2.0/genie/spaces/{space_id}/start-conversation`
   - Returns: `conversation_id` and `message_id`

2. **Poll for Completion**: GET to `/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}`
   - Poll until `status == "COMPLETED"`
   - Use exponential backoff (2s → 3s → 4.5s → ... max 10s)

3. **Get Query Results**: GET to `/api/2.0/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}/query-result/{attachment_id}`
   - Returns tabular data in `statement_response` format

## Critical Bug & Fix

### The Problem
Query results were not being displayed - `query_results` was always `null`.

### Root Cause
**INCORRECT CODE** - Looking for `attachment_id` in the wrong place:
```python
# WRONG - looking inside query object
attachment_id = query_obj.get("id")  # Returns None!
```

### The Genie API Response Structure
```json
{
  "attachments": [
    {
      "query": {
        "query": "SELECT ...",
        "description": "...",
        "statement_id": "..."
      },
      "attachment_id": "01f10eadc83f12b1b1c791357e8e815e"  // <-- HERE!
    }
  ]
}
```

**Key Insight**: The `attachment_id` is at the **attachment level**, NOT inside the `query` object!

### The Fix
```python
# CORRECT - get attachment_id from attachment level
attachment_id = attachment.get("attachment_id")
```

**File**: `databricks-app/genie_client.py:161`

## Query Results Data Structure
```json
{
  "statement_response": {
    "status": { "state": "SUCCEEDED" },
    "manifest": {
      "schema": {
        "columns": [
          { "name": "CustomerName", "type_name": "STRING" }
        ]
      }
    },
    "result": {
      "data_array": [
        ["Tailspin Toys (East Portal, CO)"],
        ["Leonardo Folliero"],
        ["Tailspin Toys (Mineral Hills, MI)"],
        ["Allan Mannik"],
        ["Tailspin Toys (Maple Shade, NJ)"]
      ]
    }
  }
}
```

## Data Extraction Logic
```python
# Get columns from manifest
columns = [col["name"] for col in stmt_response["manifest"]["schema"]["columns"]]

# Get rows from result
data_array = stmt_response["result"]["data_array"]

# Create DataFrame
df = pd.DataFrame(data_array, columns=columns)
```

## Important Streamlit Development Notes

### Module Caching Issue
**Problem**: Streamlit caches imported Python modules (like `genie_client.py`). Changes to those files don't reload automatically even with `--server.runOnSave true`.

**Symptoms**:
- Page file changes (e.g., `pages/1_🤖_Genie.py`) reload immediately ✅
- Module file changes (e.g., `genie_client.py`) don't reload ❌

**Solution**:
```bash
# Must kill and restart Streamlit server after changing genie_client.py
# Kill the server
pkill -f "streamlit run"

# Restart
cd databricks-app && ../venv/bin/streamlit run app.py --server.runOnSave true
```

**Testing Strategy**:
1. Make a visible change to the page file (e.g., change title) to verify auto-reload works
2. If that works but your code changes don't, you need to restart the server

## UI Features Implemented
✅ Natural language query input
✅ Genie's text response display
✅ Generated SQL display (collapsible)
✅ Query results table with row count
✅ Conversation history
✅ Error handling (failed/timeout)
✅ Loading spinner

## Example Queries That Work
- "list 5 customers"
- "What are the most popular stock items?"
- "Show me total orders by customer type"
- "Which customers are on credit hold?"

## Debugging Tips

### Check if query results are being fetched
Add temporary logging to see the API response:
```python
# In genie_client.py, after get_query_result()
print("DEBUG - Query result:", query_result)
```

### View full API response
Add to Streamlit page:
```python
st.json(result)  # Show full result from client
```

### Common Issues
1. **Wrong attachment_id location** - See "Critical Bug & Fix" above
2. **Module caching** - Restart Streamlit server
3. **Missing credentials** - Check .env file
4. **Timeout** - Increase `max_wait_seconds` parameter

## SQL Generation vs Execution - The Governance Game-Changer

### Discovery (2026-02-20)

**CRITICAL:** The Genie Conversation API separates SQL generation from execution into distinct API calls.

### Workflow Details

1. **Generation Phase**
   - Call: `POST /start-conversation` with natural language question
   - Returns: `conversation_id` and `message_id`
   - Poll: `GET /messages/{message_id}` until `status: COMPLETED`
   - Retrieve: Generated SQL from `attachments[].query.query`
   - **No data accessed yet**

2. **Execution Phase** (Separate API call)
   - Call: `GET /query-result/{attachment_id}`
   - Returns: Actual query results
   - **This is when data is accessed**

### Governance Implications

This separation enables:
- ✅ Parse generated SQL before execution
- ✅ Extract table.column references
- ✅ Check Atlan for PII tags
- ✅ Block query BEFORE data is accessed
- ✅ Zero wasted compute on blocked queries

### Current Implementation

`genie_client.py` currently calls both steps in `ask_question()`. For governance:
- **Needs refactoring** to separate `generate_sql()` and `execute_query()`
- See `ARCHITECTURE_GOVERNANCE.md` for full design

## Next Steps / Future Enhancements
- [x] **Document SQL generation/execution separation** ← DONE
- [ ] Refactor `genie_client.py` for 2-step governance flow
- [ ] Implement SQL parser for table.column extraction
- [ ] Connect to Atlan MCP for PII tag checks
- [ ] Add suggested questions UI (Genie returns these)
- [ ] Add data visualization options (charts)
- [ ] Export results to CSV
- [ ] Save favorite queries

## Testing Checklist
- [x] Basic query returns results
- [x] SQL is displayed correctly
- [x] Multiple queries in conversation history
- [x] Error handling (invalid queries)
- [x] UI is clean (no debug output)
- [x] New Chat UI works with sidebar controls
- [ ] Governance blocking works (awaiting implementation)
- [ ] Works on Databricks Apps (not just local)

## Deployment Notes
When deploying to Databricks Apps:
1. Environment variables must be set in Databricks Secrets
2. Use `databricks apps deploy` or Git-based deployment
3. Test the app URL after deployment
4. Verify Genie Space ID is correct for the target environment

## References
- [Databricks Genie Conversation API Docs](https://docs.databricks.com/en/generative-ai/genie-api.html)
- Wide World Importers dataset: `wide_world_importers.processed_gold` schema
- Genie Space URL: https://dbc-8d941db8-48cd.cloud.databricks.com/genie/rooms/01f10ea33fc010dcb2dc604b75ac4336

---
**Last Updated**: 2026-02-20
**Status**: ✅ Working - Production Ready
