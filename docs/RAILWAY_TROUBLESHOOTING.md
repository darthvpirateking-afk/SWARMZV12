# Railway Troubleshooting Guide

## 🔴 Common 404 Errors and Fixes

### Issue 1: Backend Shows 404 on All Routes

**Symptoms:**
- Railway build succeeds
- Deploy succeeds  
- But accessing any URL returns 404

**Cause:** Server not starting properly or wrong module path

**Fix:**
```bash
# Check Railway logs for startup errors
# In Railway dashboard → Your service → Deployments → View Logs

# Common issues:
# 1. Missing dependencies
# 2. Import errors
# 3. Wrong start command
```

**Solution:** Update `railway.toml` start command:
```toml
[deploy]
startCommand = "python -m uvicorn server:app --host 0.0.0.0 --port $PORT"
```

---

### Issue 2: Health Check Failing

**Symptoms:**
- Build succeeds
- Server starts but Railway marks as "unhealthy"
- Shows 404 or timeout

**Cause:** Health check hitting wrong path or timing out

**Fix:** Update health check settings:
```toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300  # 5 minutes for cold start
```

---

### Issue 3: Missing Environment Variables

**Symptoms:**
- 404 or 500 errors
- Logs show "KeyError" or missing config

**Fix:** Add required variables in Railway dashboard:
```bash
PYTHON_VERSION=3.13
PORT=8000  # Railway sets this automatically, but good to have
```

---

### Issue 4: Frontend 404 (Can't Find Backend)

**Symptoms:**
- Frontend loads but shows "Network Error"
- DevTools shows 404 on API calls

**Cause:** `VITE_API_BASE_URL` not set or incorrect

**Fix:** In Railway dashboard for **frontend service**:
```bash
VITE_API_BASE_URL=https://your-backend-service.up.railway.app
```

⚠️ **CRITICAL:** Must be your actual backend URL!

---

### Issue 5: "web/index.html" Not Found

**Symptoms:**
- Logs show: `FileNotFoundError: web/index.html`
- Root path (`/`) returns 404

**Cause:** Working directory is wrong or web/ folder not included

**Fix 1:** Ensure `web/` folder is in git:
```bash
git add web/
git commit -m "chore: ensure web folder is tracked"
git push
```

**Fix 2:** Update server to handle missing web folder:
```python
# In swarmz_server.py, update root handler
@app.get("/")
async def home_page():
    try:
        return FileResponse("web/index.html", media_type="text/html")
    except FileNotFoundError:
        return {"message": "SWARMZ API", "status": "running", "docs": "/docs"}
```

---

## 🧪 Test Locally First

Run this before deploying:

```bash
# Test startup
python railway_test.py

# Manual server test
python run_server.py --host 0.0.0.0 --port 8000

# In another terminal, test endpoints:
curl http://localhost:8000/health
curl http://localhost:8000/
curl http://localhost:8000/docs
```

---

## 🔍 Debug Railway Deployment

### Step 1: Check Build Logs
```
Railway Dashboard → Your Service → Deployments → Build Logs
```

Look for:
- ❌ Missing dependencies
- ❌ Python version mismatches
- ❌ File not found errors

### Step 2: Check Runtime Logs
```
Railway Dashboard → Your Service → Deployments → View Logs
```

Look for:
- ❌ Import errors
- ❌ Module not found
- ❌ Port binding issues
- ❌ Environment variable errors

### Step 3: Test Health Endpoint
```bash
curl https://your-service.up.railway.app/health
```

Should return:
```json
{"status":"ok","service":"swarmz-backend"}
```

### Step 4: Check API Docs
```bash
open https://your-service.up.railway.app/docs
```

Should show FastAPI Swagger UI.

---

## 🔧 Quick Fixes to Try

### 1. Use Alternative Start Command

Try this in `railway.toml`:
```toml
[deploy]
startCommand = "uvicorn server:app --host 0.0.0.0 --port $PORT --workers 1"
```

### 2. Disable Health Check Temporarily

To test if health check is the issue:
```toml
[deploy]
# Comment out health check
# healthcheckPath = "/health"
# healthcheckTimeout = 300
```

### 3. Add Root API Handler

Make root path always work:
```python
@app.get("/")
async def root():
    return {
        "service": "SWARMZ API",
        "status": "running",
        "health": "/health",
        "docs": "/docs",
        "version": "1.0.0"
    }
```

### 4. Check Railway Service Settings

In Railway dashboard → Settings:
- **Runtime**: Should detect Python automatically
- **Root Directory**: Should be `/` (empty for root)
- **Build Command**: Leave empty (uses nixpacks.toml)
- **Start Command**: Should match railway.toml

---

## 📋 Deployment Checklist

Before deploying, verify:

- [ ] `requirements.txt` exists and has all dependencies
- [ ] `railway.toml` has correct start command
- [ ] `server.py` or `run_server.py` exists
- [ ] `/health` endpoint is defined
- [ ] `web/` folder is committed to git
- [ ] Environment variables are set in Railway
- [ ] Python version is 3.10+ (3.13 recommended)

---

## 🆘 Still Getting 404?

### Option A: Use Railway Template
Railway has Python FastAPI templates that work out of the box.

### Option B: Simplify Start Command
Create `start.sh`:
```bash
#!/bin/bash
python -m uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
```

Then update `railway.toml`:
```toml
[deploy]
startCommand = "bash start.sh"
```

### Option C: Check for Typos
Common mistakes:
- `serve:app` instead of `server:app`
- Wrong path to Python file
- Missing `.py` extension
- Typo in module name

---

## 📞 Get Help

1. **Check Railway Logs** (most common solution)
2. **Railway Discord**: https://discord.gg/railway
3. **Railway Docs**: https://docs.railway.app/
4. **Test locally first** with `railway_test.py`

---

## ✅ Success Indicators

When working correctly, you should see:

**Build Logs:**
```
✓ Installing dependencies
✓ Building project
✓ Deploy successful
```

**Runtime Logs:**
```
LOCAL: http://127.0.0.1:8000/
LAN:   http://10.0.0.x:8000/
[COLD START] data — OK
[ENGINES] All engines loaded.
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Health Check:**
```bash
$ curl https://your-app.up.railway.app/health
{"status":"ok","service":"swarmz-backend"}
```
