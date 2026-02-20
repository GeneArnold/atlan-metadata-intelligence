# Atlan Metadata Intelligence App on Databricks

An AI-powered Databricks-native application that connects to Atlan's Metadata Lakehouse to provide natural language querying, governance checks, and actionable insights about data quality, ownership, PII exposure, and security anomalies.

## Technology Stack

- **UI Framework:** Streamlit
- **Platform:** Databricks Apps (serverless deployment)
- **Data Source:** Apache Iceberg tables (Atlan Metadata Lakehouse)
- **AI:** Claude API or Databricks Model Serving
- **Deployment:** Local development → Databricks Apps
- **CLI:** Databricks CLI

## Project Structure

```
atlan-databricks-mdlh-app/              # Parent directory (Git repo root)
├── venv/                               # Virtual environment (gitignored)
├── .git/                               # Git repository
├── .gitignore                          # Git ignore file
├── README.md                           # This file
├── WORKFLOW.md                         # Development workflow guide
├── SETUP_LOG.md                        # Complete setup documentation
├── CLAUDE.md                           # AI assistant instructions
├── PROJECT_LOG.md                      # Development log
├── project-handoff.md                  # Project handoff document
├── DEPLOYMENT_PATTERN.md               # Deployment notes
├── databricks.yml                      # Databricks Asset Bundle config
└── databricks-app/                     # ← App source (ONLY THIS syncs to Databricks)
    ├── app.py                          # Streamlit application
    ├── app.yaml                        # Databricks app configuration
    └── requirements.txt                # Python dependencies
```

**Key Design:** The parent directory contains ALL project files (docs, configs, notes). Only the `databricks-app/` subdirectory syncs to Databricks workspace. This keeps your workspace clean and allows you to maintain extensive documentation without cluttering the deployed app.

## Quick Start

### Prerequisites
- Python 3.10+
- Databricks workspace with Apps enabled
- Databricks personal access token (PAT)
- Git configured locally

### Setup (One-Time)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd atlan-databricks-mdlh-app
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   ```

3. **Install dependencies**
   ```bash
   ./venv/bin/pip install -r databricks-app/requirements.txt
   ```

4. **Configure Databricks CLI**
   ```bash
   databricks configure --token
   # Enter your Databricks host and PAT token
   ```

### Development Workflow

See **[WORKFLOW.md](WORKFLOW.md)** for detailed development instructions.

**Quick version:**

1. **Start local Streamlit server** (for testing)
   ```bash
   cd databricks-app
   ../venv/bin/streamlit run app.py
   # Visit http://localhost:8501
   ```

2. **Start Databricks sync** (in another terminal)
   ```bash
   databricks sync --watch databricks-app/ /Workspace/Users/<your-email>/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app
   ```

3. **Make changes** in `databricks-app/`
   - Test locally at http://localhost:8501
   - Files auto-sync to Databricks workspace

4. **Deploy to Databricks**
   ```bash
   databricks apps deploy atlan-metadata-intelligence
   ```

5. **Commit to Git**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

## Current Status

**Phase 1 Complete ✅** - Development workflow established and validated:
- ✅ Parent/child directory structure
- ✅ Virtual environment setup
- ✅ Local development server running
- ✅ Databricks sync working
- ✅ Deployment pipeline tested
- ✅ App running on Databricks

**Next Steps:**
- Phase 2: Atlan Metadata Lakehouse connection
- Phase 3: Check library & query engine
- Phase 4: AI layer with natural language interface
- Phase 5: Production hardening & CI/CD

## Documentation

- **[WORKFLOW.md](WORKFLOW.md)** - Daily development workflow and commands
- **[SETUP_LOG.md](SETUP_LOG.md)** - Complete setup process documentation
- **[CLAUDE.md](CLAUDE.md)** - Instructions for Claude Code AI assistant
- **[project-handoff.md](project-handoff.md)** - Comprehensive project handoff document
- **[DEPLOYMENT_PATTERN.md](DEPLOYMENT_PATTERN.md)** - Proven deployment patterns

## Databricks App Details

- **App Name:** `atlan-metadata-intelligence`
- **Workspace Path:** `/Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app`
- **Local Test URL:** http://localhost:8501
- **Databricks URL:** Available in Databricks workspace under Compute → Apps

## Development Phases

This project follows a phased approach:

1. **Phase 1:** Environment setup + workflow validation ✅
2. **Phase 2:** Atlan Metadata Lakehouse connection
3. **Phase 3:** Check library & query engine
4. **Phase 4:** AI layer with natural language interface
5. **Phase 5:** Production hardening & CI/CD

See [project-handoff.md](project-handoff.md) for detailed phase requirements.

## Key Commands

```bash
# Local development
cd databricks-app && ../venv/bin/streamlit run app.py

# Sync to Databricks (auto-watch for changes)
databricks sync --watch databricks-app/ /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app

# Deploy to Databricks
databricks apps deploy atlan-metadata-intelligence

# Git workflow
git add .
git commit -m "message"
git push origin main
```

## Support

For questions or issues:
1. Check [WORKFLOW.md](WORKFLOW.md) for common scenarios
2. Review [SETUP_LOG.md](SETUP_LOG.md) for setup details
3. Consult [project-handoff.md](project-handoff.md) for project overview

---

**Last Updated:** 2026-02-20
**Status:** Phase 1 Complete ✅
