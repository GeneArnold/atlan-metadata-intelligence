# Complete Setup Log

This document provides a detailed record of setting up the Atlan Metadata Intelligence App development environment and establishing the working deployment pattern.

**Date:** February 20, 2026
**Status:** Phase 1 Complete ✅

---

## Session Overview

**Objective:** Establish a clean, working development workflow for building a Databricks App locally and deploying it to Databricks.

**Challenge:** Initial attempt had a messy structure with app files in multiple locations, unclear what should sync to Databricks, and confusion about the deployment process.

**Solution:** Implemented a parent/child directory structure with clear separation between documentation and app code.

---

## Starting Point

### What Existed
- Databricks workspace with an existing app deployed
- App path: `/Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app`
- App name: `atlan-metadata-intelligence`
- Local directory with mixed files (some old test files)
- Git repo already initialized

### The Problem
- Old app files (`app.py`, `app.yaml`, `requirements.txt`) in root directory
- Didn't want documentation and config files syncing to Databricks
- Needed clean separation between "project files" and "app files"
- Unclear workflow for local development → Databricks deployment

---

## Step-by-Step Setup

### Step 1: Created Parent/Child Directory Structure

**Decision:** Use a parent directory for ALL project files, with a `databricks-app/` subdirectory containing ONLY the app code that syncs to Databricks.

**Action:**
```bash
mkdir -p databricks-app
```

**Result:**
```
atlan-databricks-mdlh-app/              # Parent (Git repo root)
└── databricks-app/                     # Child (syncs to Databricks)
```

**Rationale:**
- Parent can contain unlimited documentation, configs, tools
- Only `databricks-app/` syncs to Databricks workspace
- Keeps Databricks workspace clean
- Allows extensive local documentation

### Step 2: Synced Existing App from Databricks

**Goal:** Get the current working app code from Databricks workspace down to local.

**Command:**
```bash
databricks workspace export-dir \
  /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app \
  databricks-app/
```

**Result:**
- Downloaded 3 files: `app.py`, `app.yaml`, `requirements.txt`
- Files placed in `databricks-app/` subdirectory

**What Was Downloaded:**

`app.py` - Simple Streamlit "Hello World" app:
- Shows header "Hello world!!!"
- Has a slider for "Number of apps"
- Displays exponential chart based on slider

`app.yaml` - Databricks app configuration:
```yaml
command: [
  "streamlit",
  "run",
  "app.py"
]
```

`requirements.txt` - Python dependencies:
```
streamlit~=1.38.0
pandas~=2.2.3
```

### Step 3: Created Virtual Environment

**Goal:** Isolate Python dependencies from system Python.

**Action:**
```bash
cd /Users/gene.arnold/WorkSpace/atlan-databricks-mdlh-app
python3 -m venv venv
```

**Result:**
- Created `venv/` directory in parent (NOT in `databricks-app/`)
- Virtual environment gitignored (already in `.gitignore`)
- Won't sync to Databricks (not in `databricks-app/`)

**Why in parent?**
- Tool for local development only
- No need to upload to Databricks
- Keeps app directory clean

### Step 4: Installed Dependencies

**Action:**
```bash
./venv/bin/pip install -r databricks-app/requirements.txt
```

**Result:**
- Installed `streamlit` version 1.38.0
- Installed `pandas` version 2.2.3
- All dependencies available in virtual environment

**Note:** Some version conflicts with other installed packages (pyatlan), but doesn't affect this project.

### Step 5: Tested Local Streamlit Server

**Goal:** Verify app runs locally before deploying.

**Action:**
```bash
cd databricks-app
../venv/bin/streamlit run app.py
```

**Result:**
- App started successfully
- Running at http://localhost:8501
- Shows "Hello world!!!" header
- Slider and chart working correctly

**Key Learning:** Always test locally first before deploying to Databricks.

### Step 6: Started Databricks Sync

**Goal:** Enable automatic file syncing from local to Databricks workspace.

**Action:**
```bash
databricks sync --watch databricks-app/ \
  /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app
```

**Result:**
```
Action: PUT: app.py, app.yaml, requirements.txt
Uploaded requirements.txt
Uploaded app.py
Uploaded app.yaml
Initial Sync Complete
```

**What this does:**
- Watches `databricks-app/` directory
- Automatically uploads changed files to workspace
- Runs continuously in background
- **Important:** Only syncs files - does NOT deploy the app

### Step 7: Tested File Sync

**Goal:** Verify that local file changes automatically sync to Databricks.

**Test:**
```python
# Changed line in app.py:
st.header("Hello world!!!")
# To:
st.header("Hello world!!! (TEST SYNC)")
```

**Result:**
```
Action: PUT: app.py
Uploaded app.py
Complete
```

**Verification:** File successfully synced to Databricks workspace.

### Step 8: Deployed to Databricks

**Goal:** Update the running Databricks app with the changed files.

**Key Discovery:** Syncing files to workspace does NOT automatically deploy them. Must manually trigger deployment.

**Action:**
```bash
databricks apps deploy atlan-metadata-intelligence \
  --source-code-path /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app
```

**Result:**
```json
{
  "status": {
    "message": "App started successfully",
    "state": "SUCCEEDED"
  }
}
```

**Verification:** Change appeared in live Databricks app.

**Important Learning:**
- **Sync** = Updates source files in workspace (staging)
- **Deploy** = Actually restarts app with those files
- Both steps are required for changes to appear

### Step 9: Reverted Test Change

**Action:**
```python
# Reverted back to:
st.header("Hello world!!!")
```

**Result:** File automatically synced to workspace (deploy not shown, but change ready for next deployment).

### Step 10: Cleaned Up Parent Directory

**Goal:** Remove old app files that were in parent directory from earlier tests.

**Action:**
```bash
rm app.py app.yaml requirements.txt
```

**Files Removed:**
- `app.py` (old test file in root)
- `app.yaml` (old config in root)
- `requirements.txt` (old requirements in root)

**Why:** These were duplicates from earlier attempts. The real app files are now properly located in `databricks-app/`.

### Step 11: Created Documentation

**Created/Updated Files:**

1. **README.md** - Main project documentation
   - Project overview
   - Quick start guide
   - Current status
   - Links to other documentation

2. **WORKFLOW.md** - Daily development workflow
   - Complete commands for local development
   - Sync and deploy instructions
   - Common scenarios and troubleshooting
   - What syncs where

3. **DEPLOYMENT_PATTERN.md** - Proven deployment pattern
   - Why this structure works
   - Two-step deployment explained
   - Success indicators
   - Common pitfalls

4. **SETUP_LOG.md** - This file
   - Complete setup documentation
   - Every step performed
   - Rationale for decisions
   - Lessons learned

### Step 12: Verified .gitignore

**Checked:** `.gitignore` already properly configured

**Key Entries:**
```
venv/          # Virtual environment won't be committed
__pycache__/   # Python cache won't be committed
.env           # Environment variables won't be committed
.databricks/   # Databricks CLI config won't be committed
```

**Result:** No changes needed.

---

## Final Directory Structure

```
atlan-databricks-mdlh-app/              # Parent directory (Git repo root)
├── venv/                               # Virtual environment (gitignored)
├── .git/                               # Git repository
├── .gitignore                          # Git ignore file
├── .claude/                            # Claude Code settings
├── README.md                           # Main documentation
├── WORKFLOW.md                         # Development workflow guide
├── SETUP_LOG.md                        # This file
├── CLAUDE.md                           # AI assistant instructions
├── PROJECT_LOG.md                      # Development log
├── project-handoff.md                  # Project handoff document
├── DEPLOYMENT_PATTERN.md               # Deployment patterns
├── databricks.yml                      # Databricks Asset Bundle config
└── databricks-app/                     # ← ONLY THIS syncs to Databricks
    ├── app.py                          # Streamlit application
    ├── app.yaml                        # Databricks app configuration
    └── requirements.txt                # Python dependencies
```

---

## What Syncs Where

| File/Directory | Git | Databricks | Purpose |
|----------------|-----|------------|---------|
| `databricks-app/` | ✅ | ✅ | App source code |
| `venv/` | ❌ | ❌ | Local development only |
| `README.md` | ✅ | ❌ | Project documentation |
| `WORKFLOW.md` | ✅ | ❌ | Workflow documentation |
| `SETUP_LOG.md` | ✅ | ❌ | Setup documentation |
| `CLAUDE.md` | ✅ | ❌ | AI assistant docs |
| Other `.md` files | ✅ | ❌ | Documentation |
| `databricks.yml` | ✅ | ❌ | Databricks config |
| `.gitignore` | ✅ | ❌ | Git configuration |

**Key Principle:** Git tracks everything, Databricks only gets the app.

---

## Working Commands

### One-Time Setup
```bash
# Create virtual environment
python3 -m venv venv

# Install dependencies
./venv/bin/pip install -r databricks-app/requirements.txt

# Configure Databricks CLI (if not already done)
databricks configure --token
```

### Daily Development

**Terminal 1 - Local Streamlit:**
```bash
cd databricks-app
../venv/bin/streamlit run app.py
# Visit http://localhost:8501
```

**Terminal 2 - Databricks Sync:**
```bash
databricks sync --watch databricks-app/ \
  /Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app
```

**Terminal 3 - Deploy When Ready:**
```bash
databricks apps deploy atlan-metadata-intelligence
```

### Git Workflow
```bash
git add .
git commit -m "Description"
git push origin main
```

---

## Key Learnings

### 1. Parent/Child Directory Structure is Essential
**Problem:** Mixing documentation with app code creates clutter in Databricks.
**Solution:** Only sync `databricks-app/` subdirectory.
**Benefit:** Clean workspace, extensive local docs, version control everything.

### 2. Two-Step Deployment is By Design
**Initial Expectation:** Files would auto-deploy when synced.
**Reality:** Sync uploads files, deploy restarts the app.
**Why Better:** Control over when app restarts, test multiple changes first.

### 3. Local Development First
**Pattern:** Edit → Test locally → Sync → Deploy → Verify
**Benefit:** Instant feedback at http://localhost:8501, only deploy tested code.

### 4. Virtual Environment in Parent
**Location:** `venv/` in parent directory (NOT in `databricks-app/`)
**Reason:** Development tool only, no need to sync to Databricks.
**Benefit:** Keeps app directory minimal.

### 5. Documentation is Critical
**Challenge:** Easy to forget what works and why.
**Solution:** Document everything immediately while fresh.
**Files Created:** README, WORKFLOW, DEPLOYMENT_PATTERN, SETUP_LOG.

---

## Databricks App Configuration

**App Name:** `atlan-metadata-intelligence`

**Workspace Path:** `/Workspace/Users/gene.arnold@atlan.com/databricks_apps/atlan-metadata-intelligence_2026_02_20-18_30/streamlit-hello-world-app`

**Access:** Databricks Workspace → Compute → Apps → Select app

**Status Commands:**
```bash
# Check app status
databricks apps get atlan-metadata-intelligence

# View app logs
databricks apps logs atlan-metadata-intelligence
```

---

## Verification Checklist

After completing setup, verify:

- [x] Virtual environment created in parent directory
- [x] Dependencies installed from `databricks-app/requirements.txt`
- [x] App runs locally at http://localhost:8501
- [x] `databricks sync --watch` running and syncing files
- [x] Test change synced to Databricks workspace
- [x] `databricks apps deploy` successfully deployed app
- [x] Change visible in live Databricks app
- [x] Old files cleaned up from parent directory
- [x] Documentation created (README, WORKFLOW, etc.)
- [x] `.gitignore` properly configured
- [x] Directory structure clean and organized

---

## Success Metrics

**Phase 1 Complete - All Criteria Met:**

✅ **Development workflow established**
- Local development server running
- Files auto-sync to Databricks
- Deployment process documented

✅ **Parent/child structure working**
- App code in `databricks-app/`
- Documentation in parent
- Only app syncs to Databricks

✅ **End-to-end tested**
- Made a test change locally
- Verified sync to workspace
- Deployed to Databricks
- Confirmed change in live app

✅ **Fully documented**
- README with overview
- WORKFLOW with commands
- DEPLOYMENT_PATTERN with rationale
- SETUP_LOG (this file) with complete process

---

## Next Steps (Phase 2)

**Goal:** Connect to Atlan Metadata Lakehouse

**Prerequisites to gather:**
- Cloud provider (AWS/Azure/GCS)
- Iceberg catalog name in Databricks
- Whether Atlan tables are already registered
- Credentials/service principal for queries

**Tasks:**
- Create `connection.py` module
- Establish Spark/SQL connection to Iceberg tables
- Run validation query
- Display connection status in UI
- Handle connection errors gracefully

See [project-handoff.md](project-handoff.md) for detailed Phase 2 requirements.

---

## Troubleshooting Reference

### App not updating locally
- Check if Streamlit server is running
- Hard refresh browser (Cmd+Shift+R)
- Check terminal for errors

### Files not syncing to Databricks
- Verify `databricks sync --watch` is running
- Check files are in `databricks-app/` not parent
- Look for sync output in terminal

### Changes not appearing in Databricks app
- Remember: sync ≠ deploy
- Run `databricks apps deploy atlan-metadata-intelligence`
- Check deployment status

### Virtual environment issues
- Use `./venv/bin/pip` not global pip
- Or activate first: `source venv/bin/activate`
- Verify location: venv in parent, not in databricks-app/

---

**Setup Completed:** February 20, 2026
**Phase 1 Status:** ✅ Complete and Working
**Ready for:** Phase 2 - Atlan Metadata Lakehouse Connection
