# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered Databricks-native application that connects to Atlan's Metadata Lakehouse (Apache Iceberg format) to allow users to query metadata using natural language, run governance checks, and receive actionable insights about data quality, ownership, PII exposure, and security anomalies.

**Technology Stack:**
- **UI:** Streamlit
- **Platform:** Databricks Apps (serverless deployment)
- **Data Source:** Apache Iceberg tables (Atlan Metadata Lakehouse) via Spark SQL
- **AI:** Claude API or Databricks Model Serving (DBRX/Llama)
- **Deployment:** Git → Databricks Apps
- **CLI:** Databricks CLI, Databricks Asset Bundles (DABs)

## Development Workflow

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (standard)
streamlit run app/app.py

# Run with Databricks local app proxy (recommended - simulates Databricks environment)
databricks apps run-local --prepare-environment
```

### Databricks CLI Setup
```bash
# Configure authentication
databricks configure --token
# Enter: Databricks host and personal access token (PAT)

# Verify connection
databricks workspace ls /
```

### Deployment to Databricks

**CLI Deploy (fast iteration):**
```bash
# Sync files to workspace
databricks sync --watch . /Workspace/Users/<your-email>/atlan-metadata-intelligence

# Deploy the app
databricks apps deploy atlan-metadata-intelligence \
  --source-code-path /Workspace/Users/<your-email>/atlan-metadata-intelligence
```

**Git-based Deploy (recommended for production):**
1. Push to GitHub
2. In Databricks: Compute → Apps → Create App → Point to GitHub repo
3. Click Deploy

### Version Control
```bash
# After completing each phase:
git add .
git commit -m "Phase X: description"
git push
```

## Project Structure

```
atlan-metadata-intelligence/
├── .gitignore
├── README.md
├── CLAUDE.md                   # This file
├── databricks.yml              # Databricks Asset Bundle config
├── requirements.txt
├── app.yaml                    # Databricks Apps entry point config
└── app/
    ├── app.py                  # Streamlit app entry point
    ├── connection.py           # Iceberg/Spark connection handling
    ├── config.py               # Central configuration
    ├── llm.py                  # LLM abstraction layer (Claude API or Databricks)
    ├── agent.py                # Orchestrates check selection + summarization
    └── checks/
        ├── __init__.py         # Check registry
        ├── base.py             # Base Check class
        ├── ownership.py        # Ownership & stewardship checks
        ├── pii.py              # PII/sensitive data checks
        ├── quality.py          # Data quality/freshness checks
        └── security.py         # Security & access control checks
```

## Architecture

### Data Connection Layer (`connection.py`)
Establishes Spark/SQL connection to Atlan's Iceberg tables in Databricks. Atlan metadata is queryable via standard SQL:
```python
spark.sql("SELECT * FROM atlan_catalog.metadata.assets LIMIT 10")
```

### Check System (`checks/`)
Each check is a Python class that:
- Has a unique name and category (ownership | pii | quality | security)
- Contains SQL queries against Iceberg metadata tables
- Returns standardized results: `{check_name, category, status, affected_assets[], summary}`
- Registers in a central check registry

**Check Structure:**
```python
class Check:
    name: str
    category: str
    description: str
    severity: str  # critical | warning | info

    def run(self, spark) -> CheckResult:
        # SQL queries against Atlan metadata tables
        ...
```

**Check Categories:**
1. Ownership & Stewardship (no owner, inactive owners)
2. PII / Sensitive Data Exposure (tagged columns, access anomalies)
3. Data Quality / Freshness (SLA violations, failed quality checks)
4. Security & Access Control (overly permissive access, orphaned permissions)

### AI Layer (`llm.py`, `agent.py`)
The AI interaction model:
1. User submits natural language query
2. LLM receives query + manifest of available checks
3. LLM selects appropriate checks to run
4. Check engine executes selected checks
5. Results passed to LLM for plain-English summarization
6. Summary displayed in UI with actionable recommendations

**Important:** AI never writes ad-hoc SQL. It only selects from the trusted check library.

LLM provider is swappable (Claude API vs Databricks Model Serving) via configuration.

## Key Development Rules

### Sequential Phase Development
This project follows a strict phased approach:
1. **Phase 1:** Environment setup + workflow validation (simple test app)
2. **Phase 2:** Atlan Metadata Lakehouse connection
3. **Phase 3:** Check library & query engine
4. **Phase 4:** AI layer with natural language interface
5. **Phase 5:** Production hardening

**Never skip a phase.** Each phase must be completed and verified before starting the next. See `project-handoff.md` for detailed phase requirements and completion criteria.

### Security & Secrets
- **Never hardcode credentials** in code
- Use environment variables for local development
- Use Databricks Secrets for production deployment
- All sensitive values (API keys, tokens, connection strings) must be externalized

### Check Library Integrity
- The check library is the single source of truth for all queries
- New checks are added as new classes/functions + registry entries
- AI layer must never bypass the check library to write raw SQL
- All metadata queries flow through named, version-controlled checks

### Extensibility First
- Design for easy addition of new check categories
- New checks should not require refactoring existing code
- Configuration-driven where possible

## Atlan Metadata Lakehouse

Atlan stores metadata in Apache Iceberg format on cloud object storage (S3/Azure Blob/GCS). This means:
- Metadata is directly queryable via standard SQL in Databricks/Spark
- No middleware or translation layer needed
- Tables contain: assets, columns, pipelines, dashboards, users, ownership, tags, lineage, quality scores, access policies

Before implementing Phase 2, confirm with the user:
- Which cloud provider hosts the Metadata Lakehouse
- Iceberg catalog name in Databricks Unity Catalog
- Whether Atlan tables are already registered in the workspace
- What credentials/service principal to use for queries

## Testing & Validation

After every code change:
1. Test locally first using `streamlit run app/app.py`
2. Verify no errors in terminal output
3. Test UI functionality in browser
4. Deploy to Databricks and verify in production environment
5. Commit to Git with clear phase-based commit message

## CI/CD Pipeline (Phase 5)

GitHub Actions workflow for automatic deployment:
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

## Additional Resources

Complete project requirements and phase details are in `project-handoff.md`. Always reference that document for:
- Detailed phase completion criteria
- Specific check implementations required
- Configuration file templates
- Prerequisites and setup requirements
