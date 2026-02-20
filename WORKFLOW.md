# Development Workflow

This document describes the proven workflow for developing Databricks Apps locally and deploying them.

## Directory Structure

```
atlan-databricks-mdlh-app/              # Parent directory (Git repo root)
├── venv/                               # Virtual environment (gitignored)
├── .git/                               # Git repository
├── .gitignore                          # Git ignore file
├── README.md                           # Project documentation
├── CLAUDE.md                           # AI assistant instructions
├── WORKFLOW.md                         # This file
├── PROJECT_LOG.md                      # Development log
├── project-handoff.md                  # Project handoff document
├── DEPLOYMENT_PATTERN.md               # Deployment notes
├── databricks.yml                      # Databricks Asset Bundle config
└── databricks-app/                     # ← App source (ONLY THIS syncs to Databricks)
    ├── app.py                          # Streamlit application
    ├── app.yaml                        # Databricks app configuration
    └── requirements.txt                # Python dependencies
```

**Key Principle:** The parent directory contains ALL project files (docs, configs, notes). Only the `databricks-app/` subdirectory syncs to Databricks workspace.

## Setup (One-Time)

### 1. Create Virtual Environment
```bash
cd /Users/gene.arnold/WorkSpace/atlan-databricks-mdlh-app
python3 -m venv venv
```

### 2. Install Dependencies
```bash
./venv/bin/pip install -r databricks-app/requirements.txt
```

### 3. Configure Databricks CLI (if not already done)
```bash
databricks configure --token
# Enter your Databricks host and PAT token
```

## Daily Development Workflow

### Start Development Session

**Terminal 1 - Local Streamlit Server:**
```bash
cd /Users/gene.arnold/WorkSpace/atlan-databricks-mdlh-app/databricks-app
../venv/bin/streamlit run app.py
```
This runs the app locally at http://localhost:8501 for immediate testing.

**Terminal 2 - Databricks Sync (watches for file changes):**
```bash
cd /Users/gene.arnold/WorkSpace/atlan-databricks-mdlh-app
databricks sync --watch databricks-app/ /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app
```
This automatically syncs file changes to Databricks workspace.

### Make Changes

1. **Edit files** in `databricks-app/` (app.py, requirements.txt, etc.)
2. **Test locally** - Changes appear immediately at http://localhost:8501
3. **Files auto-sync** - The `databricks sync --watch` process uploads changes to workspace
4. **Deploy to Databricks** - Run this command to update the live app:
   ```bash
   databricks apps deploy atlan-metadata-intelligence
   ```
   (Can use short form after first deploy - no need to specify full source path)

5. **Verify in Databricks** - Check the app in your Databricks workspace

### Commit Changes to Git

```bash
cd /Users/gene.arnold/WorkSpace/atlan-databricks-mdlh-app
git add .
git commit -m "Description of changes"
git push origin main
```

**Important:** Git commits the entire parent directory (docs + app code), but Databricks only syncs `databricks-app/`.

## Databricks App Details

- **App Name:** `atlan-metadata-intelligence`
- **Workspace Path:** `/Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app`
- **Deployment Command:** `databricks apps deploy atlan-metadata-intelligence`

## Key Commands Reference

### Local Development
```bash
# Run app locally
cd databricks-app && ../venv/bin/streamlit run app.py

# Install new Python package
./venv/bin/pip install package-name
# Then add to databricks-app/requirements.txt
```

### Databricks Sync & Deploy
```bash
# Start watching for changes (run once, keeps running)
databricks sync --watch databricks-app/ /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app

# Deploy app to Databricks (run after making changes)
databricks apps deploy atlan-metadata-intelligence

# Export app from Databricks to local (if needed)
databricks workspace export-dir /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app databricks-app/
```

### Git
```bash
# Check status
git status

# Commit changes
git add .
git commit -m "message"
git push origin main
```

## Common Scenarios

### Adding a New Python Package
1. Add to `databricks-app/requirements.txt`
2. Install locally: `./venv/bin/pip install -r databricks-app/requirements.txt`
3. Sync will automatically upload the updated requirements.txt
4. Deploy: `databricks apps deploy atlan-metadata-intelligence`

### Creating Supporting Documentation
1. Create markdown files in the **parent directory** (not in databricks-app/)
2. They'll be tracked in Git but won't sync to Databricks
3. Examples: README.md, NOTES.md, ARCHITECTURE.md

### Troubleshooting

**Local app not updating:**
- Streamlit auto-reloads on file changes
- If it doesn't, check the terminal for errors
- Hard refresh browser (Cmd+Shift+R or Ctrl+Shift+R)

**Databricks app not updating:**
- Changes to workspace files don't automatically update the running app
- Must run: `databricks apps deploy atlan-metadata-intelligence`
- Check deployment status in Databricks UI: Compute → Apps

**Sync not working:**
- Check that `databricks sync --watch` process is still running
- Restart it if needed
- Verify file is in `databricks-app/` not parent directory

## What Gets Synced Where

| Location | Syncs to Databricks? | Tracked in Git? |
|----------|---------------------|-----------------|
| `databricks-app/` | ✅ Yes | ✅ Yes |
| Parent directory docs | ❌ No | ✅ Yes |
| `venv/` | ❌ No (gitignored) | ❌ No |
| `.git/` | ❌ No | N/A |

---

**Last Updated:** 2026-02-20
**Status:** Phase 1 Complete ✅
