# Proven Databricks Apps Deployment Pattern

This document captures the **working pattern** for deploying Streamlit apps to Databricks Apps, based on our successful Phase 1 deployment.

## ✅ Working Directory Structure

```
atlan-databricks-mdlh-app/              # Parent directory (Git repo root)
├── venv/                               # Virtual environment (gitignored)
├── .git/                               # Git repository
├── .gitignore                          # Git ignore file
├── README.md                           # Project documentation
├── WORKFLOW.md                         # Development workflow guide
├── SETUP_LOG.md                        # Complete setup documentation
├── CLAUDE.md                           # AI assistant instructions
├── PROJECT_LOG.md                      # Development log
├── project-handoff.md                  # Project handoff document
├── DEPLOYMENT_PATTERN.md               # This file
├── databricks.yml                      # Databricks Asset Bundle config
└── databricks-app/                     # ← ONLY THIS syncs to Databricks
    ├── app.py                          # Streamlit application
    ├── app.yaml                        # Databricks app configuration
    └── requirements.txt                # Python dependencies
```

**Key Design Principle:** Parent/child structure allows extensive documentation and tooling in the parent directory while keeping the Databricks workspace clean with only essential app files.

## ✅ Working app.yaml

```yaml
command: [
  "streamlit",
  "run",
  "app.py"
]
```

**Key Points:**
- Simple command pointing to `app.py` in the app directory
- No need for `--server.headless` flag (works without it)
- Port is automatically managed by Databricks

## ✅ Working requirements.txt

```
streamlit~=1.38.0
pandas~=2.2.3
```

**Key Points:**
- Use version ranges (`~=`) not exact versions for flexibility
- Keep minimal - only add what you need
- Databricks installs these automatically on deployment
- Additional packages can be added as needed

## ✅ Working Deployment Workflow

### **Step 1: Sync Files to Databricks Workspace**

```bash
databricks sync --watch databricks-app/ /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app
```

**What this does:**
- Watches `databricks-app/` directory for changes
- Automatically uploads changed files to Databricks workspace
- Keeps running in background (use separate terminal)
- **Important:** This ONLY syncs files - it does NOT deploy the app

**Success indicators:**
- Initial sync shows: `Initial Sync Complete`
- File changes show: `Action: PUT: app.py` followed by `Complete`

### **Step 2: Deploy the App**

```bash
databricks apps deploy atlan-metadata-intelligence
```

**What this does:**
- Takes the synced files from workspace
- Builds and deploys the app
- Restarts the app with new code
- **This step is REQUIRED** for changes to appear in the running app

**Success indicators:**
```json
{
  "status": {
    "message": "App started successfully",
    "state": "SUCCEEDED"
  }
}
```

## ✅ Complete Development Workflow

### Terminal 1: Local Development Server
```bash
cd databricks-app
../venv/bin/streamlit run app.py
```
- Runs app at http://localhost:8501
- For rapid testing and iteration
- Auto-reloads on file changes

### Terminal 2: Databricks Sync (Background)
```bash
databricks sync --watch databricks-app/ /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app
```
- Keeps running to auto-sync files
- Monitors for changes
- Uploads to workspace automatically

### Terminal 3: Deploy Commands
```bash
# When ready to update Databricks app:
databricks apps deploy atlan-metadata-intelligence

# Check app status:
databricks apps get atlan-metadata-intelligence
```

## ✅ Why This Pattern Works

### Parent/Child Directory Structure
**Problem:** Don't want documentation, config files, and development tools syncing to Databricks
**Solution:** Only sync `databricks-app/` subdirectory, keep everything else in parent

**Benefits:**
- Clean Databricks workspace (only app files)
- Extensive local documentation without clutter
- Virtual environment stays local (not uploaded)
- Git tracks everything, Databricks gets only what it needs

### Two-Step Deployment (Sync + Deploy)
**Problem:** Initial expectation was files would auto-deploy
**Reality:** Databricks Apps uses a two-step process by design

**Step 1 - Sync:** Updates source files in workspace (staging)
**Step 2 - Deploy:** Builds and restarts app with those files

**Why it's better:**
- Control when app restarts (not on every typo)
- Test multiple changes before deploying
- Safer production deployments

### Local Development First
**Pattern:** Always test locally before deploying to Databricks

**Workflow:**
1. Edit files in `databricks-app/`
2. Test at http://localhost:8501 (instant feedback)
3. When satisfied, deploy to Databricks
4. Verify in Databricks environment

## ✅ Key Commands Reference

### Setup (One-Time)
```bash
# Create virtual environment
python3 -m venv venv

# Install dependencies
./venv/bin/pip install -r databricks-app/requirements.txt

# Configure Databricks CLI
databricks configure --token
```

### Daily Development
```bash
# Run locally (Terminal 1)
cd databricks-app && ../venv/bin/streamlit run app.py

# Start sync (Terminal 2)
databricks sync --watch databricks-app/ /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app

# Deploy when ready (Terminal 3)
databricks apps deploy atlan-metadata-intelligence
```

### Git Workflow
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

## ✅ Verification Checklist

After deployment, verify:
- [ ] Deployment status shows `"SUCCEEDED"`
- [ ] App status shows `"RUNNING"`
- [ ] App URL is accessible in Databricks workspace
- [ ] Changes appear in the live app
- [ ] No errors in app logs

Check app status:
```bash
databricks apps get atlan-metadata-intelligence
```

## ❌ Common Pitfalls to Avoid

1. **Expecting auto-deployment** - Sync does NOT deploy, must run `databricks apps deploy`
2. **Syncing entire parent directory** - Only sync `databricks-app/` subdirectory
3. **Forgetting to activate venv** - Use `./venv/bin/pip` or activate first
4. **Not testing locally first** - Always test at http://localhost:8501 before deploying
5. **Including venv/ in sync** - Keep venv in parent (gitignored, won't sync)

## 🔑 Success Indicators

### Sync Working
```
Action: PUT: app.py, app.yaml, requirements.txt
Uploaded requirements.txt
Uploaded app.py
Uploaded app.yaml
Initial Sync Complete
```

### Deployment Successful
```json
{
  "status": {
    "message": "App started successfully",
    "state": "SUCCEEDED"
  }
}
```

### App Running
- Status: `RUNNING`
- Compute: `ACTIVE`
- URL accessible in Databricks workspace

## 📊 Databricks App Details

**App Name:** `atlan-metadata-intelligence`

**Workspace Path:** `/Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app`

**Access:** Databricks Workspace → Compute → Apps → `atlan-metadata-intelligence`

## 🎯 Best Practices

1. **Always test locally first** using `streamlit run app.py`
2. **Keep sync running** in background during development
3. **Deploy intentionally** when changes are tested and ready
4. **Commit to Git regularly** to backup all work
5. **Use parent directory** for all documentation and configs
6. **Keep databricks-app/ minimal** with only essential app files

---

**Last Updated:** 2026-02-20
**Status:** Phase 1 Complete ✅
**This pattern is proven and working!**
