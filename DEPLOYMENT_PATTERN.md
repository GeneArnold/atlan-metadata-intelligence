# Proven Databricks Apps Deployment Pattern

This document captures the **working pattern** for deploying Streamlit apps to Databricks Apps, based on our successful Phase 1 deployment.

## ✅ Working App Structure

```
atlan-metadata-intelligence/
├── .gitignore
├── README.md
├── CLAUDE.md
├── PROJECT_LOG.md
├── DEPLOYMENT_PATTERN.md    # This file
├── project-handoff.md
├── databricks.yml
├── app.py                    # ✅ IN ROOT (not in subdirectory)
├── app.yaml                  # ✅ IN ROOT
└── requirements.txt          # ✅ IN ROOT
```

**Key Point:** All three essential files (`app.py`, `app.yaml`, `requirements.txt`) must be in the **root directory**.

## ✅ Working app.yaml

```yaml
command: ["streamlit", "run", "app.py", "--server.port", "8501", "--server.headless", "true"]
```

**Key Points:**
- Points to `app.py` (not `app/app.py`)
- Includes `--server.headless true` flag for Databricks
- Uses port 8501 (Databricks standard)

## ✅ Working requirements.txt

```
streamlit>=1.32.0
```

**Key Points:**
- Use version ranges (`>=`) not exact versions
- Keep minimal - only add what you need
- Databricks installs these automatically on deployment

## ✅ Working Deployment Method

### **Option 1: Databricks UI (RECOMMENDED for initial setup)**

1. In Databricks Workspace → Compute → Apps → Create App
2. Configure:
   - **Name:** `atlan-metadata-intelligence`
   - **Source Type:** Git repository
   - **Repository URL:** `https://github.com/GeneArnold/atlan-metadata-intelligence`
   - **Branch:** `main`
3. Click **Create & Deploy**
4. Wait for "App started successfully" status

**Why this works:**
- Databricks clones repo directly (clean source)
- Automatically detects `app.yaml`
- Installs dependencies from `requirements.txt`
- No file format issues (vs CLI upload)

### **Option 2: CLI Deploy (for updates after initial setup)**

```bash
# Only after app exists via UI
databricks apps deploy atlan-metadata-intelligence \
  --source-code-path /Workspace/Users/<your-email>/path-to-app
```

## ✅ Development Workflow

1. **Develop locally:**
   ```bash
   streamlit run app.py
   ```

2. **Test locally:**
   - Verify app loads at `http://localhost:8501`
   - Test all functionality

3. **Commit to Git:**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   ```

4. **Deploy to Databricks:**
   - If first time: Use Databricks UI (Option 1)
   - If updating existing: Redeploy through UI or CLI

## ✅ Verification Checklist

After deployment, verify:
- [ ] App status shows "SUCCEEDED"
- [ ] App status shows "RUNNING"
- [ ] Compute status shows "ACTIVE"
- [ ] App URL is accessible (returns 401 when not logged in - this is correct!)
- [ ] App displays correctly when accessed while logged into Databricks

## ❌ Common Pitfalls to Avoid

1. **Nested directory structure** - Don't put app.py in `app/` subdirectory
2. **CLI file upload** - Files get wrong format (NOTEBOOK vs FILE)
3. **Missing --server.headless flag** - App won't start in Databricks
4. **Wrong app.yaml path** - Must point to `app.py` not `app/app.py`
5. **Including venv/ in uploads** - Massive unnecessary upload (use .gitignore)

## 🔑 Success Indicators

```json
{
  "app_status": {
    "message": "App has status: App is running",
    "state": "RUNNING"
  },
  "compute_status": {
    "message": "App compute is running.",
    "state": "ACTIVE"
  },
  "active_deployment": {
    "status": {
      "message": "App started successfully",
      "state": "SUCCEEDED"
    }
  }
}
```

## 📊 Working App Example

**Live URL:** https://atlan-metadata-intelligence-5448350934783685.aws.databricksapps.com

**GitHub Repo:** https://github.com/GeneArnold/atlan-metadata-intelligence

Use this as the reference for all future development!

---

_Last Updated: February 20, 2026_
_Status: Phase 1 Complete ✅_
