# Project Handoff: Atlan Metadata Intelligence App on Databricks
> **For Claude Code** — Read this entire document before writing a single line of code. This is the source of truth for the project.

---

## Who This Is For
This document is a complete handoff to Claude Code to build, phase by phase, an AI-powered metadata intelligence application. The app will run natively inside Databricks and allow users to converse with Atlan's Metadata Lakehouse — surfacing anomalies, security risks, data quality issues, ownership gaps, and PII exposure using natural language.

This document is written to be consumed by Claude Code directly. Follow the phases in order. Do not skip ahead. Each phase must be verified before moving to the next.

---

## Project Overview

### What We Are Building
An AI-powered Databricks-native application that connects to the Atlan Metadata Lakehouse (stored in Apache Iceberg format) and allows users to:
- Ask natural language questions about their metadata ("What tables have no owner?")
- Run named security and governance checks ("Run the PII exposure checks")
- Receive plain-English summaries of findings with actionable remediation suggestions
- Drill into specific flagged assets

### Technology Stack
- **App Framework:** Streamlit (primary), with Flask as a fallback option
- **Platform:** Databricks Apps (serverless, native deployment)
- **Data Layer:** Apache Iceberg tables exposed by Atlan's Metadata Lakehouse, queryable via Spark SQL / Databricks SQL
- **AI Layer:** Claude API (via Anthropic) or Databricks Model Serving (DBRX/Llama) — TBD in later phase
- **Deployment:** Local development → Git (GitHub) → Databricks Apps deployment
- **CLI Tooling:** Databricks CLI, Databricks Asset Bundles (DABs)
- **Version Control:** GitHub

### The Metadata Source: Atlan's Metadata Lakehouse
Atlan stores metadata in **Apache Iceberg format** on cloud object storage (S3, Azure Blob, or GCS). This means:
- Metadata is queryable via standard SQL directly in Databricks/Spark
- No middleware or translation layer needed
- Tables contain information about assets: tables, columns, pipelines, dashboards, users, ownership, tags, lineage, quality scores, access policies, and more
- Atlan also exposes metadata via REST API and MCP servers as secondary access methods

### Check Categories (All Must Be Extensible)
1. **Ownership & Stewardship Gaps** — Assets with no assigned owner, no steward, or inactive owners
2. **PII / Sensitive Data Exposure** — Tagged PII columns accessible to broad or unauthorized groups
3. **Data Quality / Freshness Issues** — Tables not updated within expected SLA windows, failed quality checks
4. **Security & Access Control Anomalies** — Overly permissive access, orphaned permissions, policy violations
5. *(Open-ended — new check categories must be addable without refactoring)*

---

## Development Philosophy
- **Build locally, push to Databricks.** Claude Code builds and tests everything on the local machine first.
- **Git is the source of truth.** All code lives in a GitHub repository. Databricks deploys from Git.
- **Phases are sequential.** Complete and verify each phase before starting the next.
- **No hardcoded secrets.** All credentials, tokens, and connection strings go in environment variables or Databricks Secrets.
- **Extensibility first.** The check system must be designed so new checks can be added as simple config or function additions, not refactors.

---

## Phase 1: Environment Setup & Workflow Validation
> **Goal:** Establish the complete local → Git → Databricks deployment pipeline. The app built in this phase is a throwaway "Hello World" Streamlit app. It has nothing to do with the final product. Its only purpose is to prove the workflow functions end to end.

### 1.1 Prerequisites (User Must Have These Ready)
Before Claude Code begins, the following must be in place. Claude Code should verify these exist and prompt the user if anything is missing:

- [ ] Python 3.10+ installed locally
- [ ] `pip` or `uv` available
- [ ] A GitHub account and a new empty repository created for this project
- [ ] A Databricks workspace with **Databricks Apps enabled** (workspace admin must enable this under Previews if not already on)
- [ ] A Databricks personal access token (PAT) or OAuth configured
- [ ] Git installed and configured locally (`git config --global user.name` etc.)
- [ ] VS Code (recommended) or preferred IDE

### 1.2 Databricks CLI Setup
Claude Code will walk through:

1. Install the Databricks CLI:
   ```bash
   pip install databricks-cli
   # or for the newer v2 CLI:
   curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh
   ```

2. Configure authentication:
   ```bash
   databricks configure --token
   # Prompts for: Databricks host (https://your-workspace.azuredatabricks.net or .cloud.databricks.com), and PAT token
   ```

3. Verify connection:
   ```bash
   databricks workspace ls /
   ```

### 1.3 Project Repository Structure
Claude Code will create the following local directory structure:

```
atlan-metadata-intelligence/
├── .gitignore
├── README.md
├── databricks.yml              # Databricks Asset Bundle config
├── requirements.txt
├── app.yaml                    # Databricks Apps entry point config
└── app/
    └── app.py                  # Streamlit app entry point
```

**This structure must be maintained and extended throughout all phases.** Do not restructure without documenting why.

### 1.4 The Phase 1 Streamlit App
The test app is intentionally simple. It must:
- Display a title: "Databricks + Streamlit: Workflow Test"
- Show the current timestamp (to prove it's live, not cached)
- Display a text input and a button that echoes back whatever the user typed
- Show a success banner confirming "Connected to Databricks Apps ✓"

This is not a placeholder — it must actually run both locally and in Databricks before Phase 2 begins.

**`app/app.py`** — Claude Code writes this file.

**`app.yaml`** — Required by Databricks Apps to know how to start the app:
```yaml
command: ["streamlit", "run", "app/app.py", "--server.port", "8501"]
```

**`databricks.yml`** — Databricks Asset Bundle definition:
```yaml
bundle:
  name: atlan-metadata-intelligence

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: <DATABRICKS_HOST>  # User fills this in

  prod:
    mode: production
    workspace:
      host: <DATABRICKS_HOST>  # User fills this in

resources:
  apps:
    atlan_metadata_intelligence:
      name: "atlan-metadata-intelligence"
      description: "AI-powered Atlan Metadata Intelligence App"
      source_code_path: .
```

**`requirements.txt`** — Phase 1 minimal:
```
streamlit>=1.32.0
```

### 1.5 Local Run & Test
Claude Code will provide the exact commands to run the app locally:

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (standard)
streamlit run app/app.py

# OR run with Databricks local app proxy (recommended - simulates Databricks environment)
databricks apps run-local --prepare-environment
```

User verifies the app loads at `http://localhost:8501` (or `http://localhost:8001` with the proxy).

### 1.6 Push to GitHub
```bash
git init
git remote add origin https://github.com/<your-org>/<your-repo>.git
git add .
git commit -m "Phase 1: initial Streamlit test app"
git push -u origin main
```

### 1.7 Deploy to Databricks from Git
Two options — Claude Code will walk through both and let the user choose:

**Option A — CLI Deploy (fastest for iteration):**
```bash
# Sync local files to Databricks workspace
databricks sync --watch . /Workspace/Users/<your-email>/atlan-metadata-intelligence

# Deploy the app
databricks apps deploy atlan-metadata-intelligence \
  --source-code-path /Workspace/Users/<your-email>/atlan-metadata-intelligence
```

**Option B — Git-based Deploy (recommended for ongoing workflow):**
1. In Databricks workspace → Compute → Apps → Create App
2. Point it at the GitHub repo and `main` branch
3. Click Deploy
4. Future deploys: push to GitHub → click Deploy in Databricks

### 1.8 Phase 1 Completion Criteria
Do not proceed to Phase 2 until ALL of the following are true:
- [ ] App runs locally without errors
- [ ] App is deployed and accessible via its Databricks Apps URL
- [ ] The timestamp updates on refresh (proving it's live)
- [ ] The echo input works
- [ ] Git repo is up to date with deployed code
- [ ] User confirms everything works

---

## Phase 2: Atlan Metadata Lakehouse Connection
> **Goal:** Establish a live read connection from the Databricks app to Atlan's Iceberg metadata tables. Validate that SQL queries return real metadata.

### 2.1 What Needs to Be Figured Out First
Before Claude Code writes connection code, the user needs to answer:
- What cloud is the Atlan Metadata Lakehouse on? (AWS S3 / Azure Blob / GCS)
- What is the Iceberg catalog name in Databricks Unity Catalog or external catalog?
- Does the Databricks workspace already have the Atlan Iceberg tables registered, or does this need to be configured?
- What credentials/service principal does the app use to query the tables?

Claude Code will prompt the user for these answers before writing Phase 2 code.

### 2.2 Connection Approach
Atlan's Metadata Lakehouse exposes Iceberg tables. In Databricks, these are queryable via:

```python
# Using Databricks SQL Connector or Spark session
from databricks import sql
# OR
spark.sql("SELECT * FROM atlan_catalog.metadata.assets LIMIT 10")
```

Claude Code will write a `connection.py` module that:
- Establishes the Spark/SQL connection
- Runs a validation query to confirm the tables are accessible
- Handles connection errors gracefully with user-friendly messages in the UI

### 2.3 Updated Project Structure
```
atlan-metadata-intelligence/
├── .gitignore
├── README.md
├── databricks.yml
├── requirements.txt
├── app.yaml
└── app/
    ├── app.py                  # Updated with connection status panel
    ├── connection.py           # NEW: handles Iceberg/Spark connection
    └── config.py               # NEW: central config (table names, settings)
```

### 2.4 Phase 2 Completion Criteria
- [ ] App successfully connects to Atlan Iceberg tables
- [ ] A test query runs and returns real data displayed in the UI
- [ ] Connection errors surface clearly in the UI (not just terminal crashes)
- [ ] No credentials are hardcoded anywhere

---

## Phase 3: Check Library & Query Engine
> **Goal:** Build the library of named metadata checks and the engine that runs them. No AI yet — pure SQL-based checks with results displayed in the UI.

### 3.1 Check Architecture
Each check is a Python class/function that:
- Has a unique name and category
- Contains one or more SQL queries against the Iceberg metadata tables
- Returns a standardized result object: `{check_name, category, status, affected_assets[], summary}`
- Can be registered in a central check registry

Example check structure:
```python
class Check:
    name: str
    category: str  # ownership | pii | quality | security
    description: str
    severity: str  # critical | warning | info
    
    def run(self, spark) -> CheckResult:
        ...
```

### 3.2 Initial Check Library (Starting Set)
**Ownership & Stewardship:**
- Assets with no owner assigned
- Assets with no steward assigned
- Assets owned by deactivated/removed users

**PII / Sensitive Data:**
- PII-tagged columns with no data classification policy
- PII columns accessible to groups broader than expected
- Untagged columns matching PII naming patterns (ssn, email, phone, dob, etc.)

**Data Quality / Freshness:**
- Tables not updated within their defined SLA window
- Tables with failed quality check scores below threshold
- Tables with no quality checks defined at all

**Security & Access:**
- Assets with public/open access that are tagged sensitive
- Orphaned permissions (user no longer in org)
- Tables with no access policy defined

### 3.3 Updated Project Structure
```
atlan-metadata-intelligence/
├── app/
│   ├── app.py
│   ├── connection.py
│   ├── config.py
│   └── checks/
│       ├── __init__.py         # Check registry
│       ├── base.py             # Base Check class
│       ├── ownership.py        # Ownership checks
│       ├── pii.py              # PII checks
│       ├── quality.py          # Quality/freshness checks
│       └── security.py         # Security checks
```

### 3.4 Phase 3 Completion Criteria
- [ ] All initial checks run successfully against real Atlan metadata
- [ ] Results display in the Streamlit UI grouped by category
- [ ] Each result shows: check name, severity, number of affected assets, list of flagged assets
- [ ] New checks can be added by creating a new function/class and registering it — no other changes needed

---

## Phase 4: AI Layer — Natural Language Interface
> **Goal:** Add the conversational AI layer. Users can now type natural language requests and the AI interprets them, selects the right checks, runs them, and summarizes the findings.

### 4.1 AI Interaction Model
The AI loop works as follows:
1. User types a natural language request in the chat input
2. LLM receives the message + a manifest of all available checks (name, description, category)
3. LLM returns a structured response: which checks to run, in what order, and any clarifying parameters
4. The check engine runs the selected checks
5. Results are passed back to the LLM for summarization
6. LLM returns a plain-English summary with severity, findings, and recommended actions
7. Results and summary display in the UI
8. User can ask follow-up questions

### 4.2 LLM Options (To Be Decided With User)
- **Anthropic Claude API** — via `anthropic` Python SDK, requires API key stored in Databricks Secrets
- **Databricks Model Serving** — DBRX or Llama hosted natively in Databricks, uses workspace credentials automatically (preferred for data residency / security)
- **Both** — configurable per deployment target

Claude Code will not hardcode this decision. It will build an abstraction layer (`llm.py`) so the underlying model can be swapped.

### 4.3 Updated Project Structure
```
atlan-metadata-intelligence/
├── app/
│   ├── app.py                  # Updated with chat interface
│   ├── connection.py
│   ├── config.py
│   ├── llm.py                  # NEW: LLM abstraction layer
│   ├── agent.py                # NEW: orchestrates check selection + summarization
│   └── checks/
│       └── ...
```

### 4.4 Phase 4 Completion Criteria
- [ ] User can type "run the security checks" and the right checks execute automatically
- [ ] User can ask "what has no owner?" and get a plain-English answer with affected assets listed
- [ ] Conversation history is maintained within a session
- [ ] The AI never writes ad-hoc SQL directly — it only selects from the trusted check library
- [ ] LLM provider is swappable via config, not a code change

---

## Phase 5: Polish, Hardening & Production Readiness
> **Goal:** Make the app production-worthy. Proper error handling, logging, security, and UX polish.

### 5.1 Items to Address
- Databricks Secrets integration for all credentials (no env files in production)
- Proper logging to Databricks logging infrastructure
- Rate limiting / timeout handling for long-running checks
- UI polish: severity color coding, export results to CSV, check history within session
- DABs-based CI/CD: GitHub Actions triggers Databricks bundle deploy on merge to main
- Role-based access: who can run which checks (leverages Databricks Unity Catalog permissions)

### 5.2 CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Databricks CLI
        run: pip install databricks-cli
      - name: Deploy Bundle
        run: databricks bundle deploy --target prod
        env:
          DATABRICKS_HOST: ${{ secrets.DATABRICKS_HOST }}
          DATABRICKS_TOKEN: ${{ secrets.DATABRICKS_TOKEN }}
```

---

## Important Rules for Claude Code

1. **Never skip a phase.** If Phase 1 isn't working, do not write Phase 2 code.
2. **Always ask before assuming.** If a configuration value, table name, or credential is unknown, stop and ask the user. Do not guess.
3. **No secrets in code.** Ever. Use environment variables locally, Databricks Secrets in production.
4. **Every file you create must be explained.** Tell the user what each file does and why it exists.
5. **Test commands must be provided.** After every code change, give the user the exact command to run to verify it works.
6. **The check library is sacred.** The AI layer must never bypass the check library to write raw SQL. All queries go through named, version-controlled checks.
7. **Git commit after every phase.** Provide the exact git commands. Keep the repo clean and current.
8. **If something is unclear in this document, ask before proceeding.**

---

## Current Status
- [ ] Phase 1 — Environment Setup & Workflow Validation
- [ ] Phase 2 — Atlan Metadata Lakehouse Connection
- [ ] Phase 3 — Check Library & Query Engine
- [ ] Phase 4 — AI Layer — Natural Language Interface
- [ ] Phase 5 — Polish, Hardening & Production Readiness

**Start with Phase 1. Begin by verifying the prerequisites listed in section 1.1.**
