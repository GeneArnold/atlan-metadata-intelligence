# Atlan Metadata Intelligence App on Databricks

An AI-powered Databricks-native application that connects to Atlan's Metadata Lakehouse to provide natural language querying, governance checks, and actionable insights about data quality, ownership, PII exposure, and security anomalies.

## Technology Stack

- **UI Framework:** Streamlit
- **Platform:** Databricks Apps (serverless deployment)
- **Data Source:** Apache Iceberg tables (Atlan Metadata Lakehouse)
- **AI:** Claude API or Databricks Model Serving
- **Deployment:** Git → Databricks Apps
- **CLI:** Databricks CLI, Databricks Asset Bundles (DABs)

## Quick Start

### Prerequisites
- Python 3.10+
- Databricks workspace with Apps enabled
- Databricks personal access token (PAT)
- Git configured locally

### Local Development
```bash
# Create and activate virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run locally
streamlit run app/app.py

# OR run with Databricks local app proxy
databricks apps run-local --prepare-environment
```

### Deploy to Databricks

**Option 1: CLI Deploy**
```bash
# Sync files to workspace
databricks sync --watch . /Workspace/Users/<your-email>/atlan-metadata-intelligence

# Deploy the app
databricks apps deploy atlan-metadata-intelligence \
  --source-code-path /Workspace/Users/<your-email>/atlan-metadata-intelligence
```

**Option 2: Git-based Deploy (Recommended)**
1. Push to GitHub: `git push origin main`
2. In Databricks: Compute → Apps → Create App
3. Point to GitHub repo and main branch
4. Click Deploy

## Project Structure

```
atlan-metadata-intelligence/
├── .gitignore
├── README.md
├── CLAUDE.md                   # AI assistant guidance
├── PROJECT_LOG.md              # Detailed development log
├── databricks.yml              # Databricks Asset Bundle config
├── requirements.txt
├── app.yaml                    # Databricks Apps entry point
└── app/
    └── app.py                  # Streamlit app entry point
```

## Development Phases

This project follows a phased approach:
- **Phase 1:** Environment setup + workflow validation ✅ (Current)
- **Phase 2:** Atlan Metadata Lakehouse connection
- **Phase 3:** Check library & query engine
- **Phase 4:** AI layer with natural language interface
- **Phase 5:** Production hardening & CI/CD

## Current Status

Phase 1 - Hello World test app to validate the deployment workflow.

For detailed development logs and steps, see `PROJECT_LOG.md`.
