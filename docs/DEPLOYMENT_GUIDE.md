# 🚀 Deploying SWARMZ to Production

## Current Setup: Render

### Backend (Python)
- **Service**: `swarmzv10`
- **URL**: `https://swarmzv10.onrender.com`
- **Health**: `https://swarmzv10.onrender.com/health`

### Frontend (Static)
- **Service**: `swarmz-frontend`  
- **Served via**: Render static site

### Configuration
The backend **already has CORS enabled** (allows all origins), so connection should work once URLs are corrected.

## ✅ **Fixed Issues**

1. **Frontend URL corrected** in `frontend/src/api/client.ts`
   - Removed malformed `https://https-swarmzv10-onrender-com.onrender.com`
   - Now uses environment variable `VITE_API_BASE_URL`

2. **Environment files added:**
   - `frontend/.env.production` - production API URL
   - `frontend/.env.development` - local dev URL

3. **Render config updated** in `render.yaml`:
   - Added `VITE_API_BASE_URL` env var for frontend build
   - Set Python version to 3.13
   - Added security headers

## 🔧 **Setup Instructions**

### 1. Update Render Environment Variables
In your Render dashboard for `swarmz-frontend`:
1. Go to Environment tab
2. Add: `VITE_API_BASE_URL` = `https://swarmzv10.onrender.com`
3. Save and redeploy

### 2. Verify Backend is Running
```bash
curl https://swarmzv10.onrender.com/health
# Should return: {"status":"ok"}
```

### 3. Test API Endpoints
```bash
# Test missions endpoint
curl https://swarmzv10.onrender.com/v1/missions

# Test with API docs
open https://swarmzv10.onrender.com/docs
```

### 4. Deploy Changes
```bash
git add .
git commit -m "fix: correct Render backend/frontend connection"
git push origin copilot/fix-missing-autofind-agent-result
```

## 🌟 **Better Alternatives to Render**

### Option 1: **Vercel** (Recommended for Full-Stack)
**Pros:**
- ✅ Better monorepo support
- ✅ Automatic frontend/serverless functions
- ✅ Global CDN
- ✅ Zero-config TypeScript
- ✅ Better logs/analytics
- ✅ Faster deploys

**Setup:**
```bash
npm i -g vercel
vercel login
vercel
```

Create `vercel.json`:
```json
{
  "buildCommand": "cd frontend && npm run build",
  "outputDirectory": "frontend/dist",
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.13"
    }
  }
}
```

### Option 2: **Railway** (Best for Python + Static)
**Pros:**
- ✅ Simpler than Render
- ✅ Better Python support
- ✅ Built-in Redis/Postgres
- ✅ Better monitoring
- ✅ No cold starts

**Setup:**
```bash
npm i -g @railway/cli
railway login
railway init
railway up
```

### Option 3: **Fly.io** (Best for Control)
**Pros:**
- ✅ Docker-based (full control)
- ✅ Global edge deployment
- ✅ Built-in Postgres
- ✅ Better pricing

**Setup:**
```bash
fly launch
fly deploy
```

### Option 4: **Cloudflare Pages + Workers** (Best for Scale)
**Pros:**
- ✅ Free tier very generous
- ✅ Global edge network
- ✅ Workers for backend API
- ✅ Zero cold starts

## 📊 **Comparison**

| Platform | Python Support | Static Site | Database | Price | Best For |
|----------|---------------|-------------|----------|-------|----------|
| **Render** | ✅ Good | ✅ Good | ✅ Postgres | $$ | Current setup |
| **Vercel** | ⚠️ Serverless only | ✅✅ Excellent | ❌ BYO | $ | Monorepos |
| **Railway** | ✅✅ Excellent | ✅ Good | ✅ Built-in | $$ | Python apps |
| **Fly.io** | ✅✅ Excellent | ✅ Good | ✅ Built-in | $ | Docker/Control |
| **Cloudflare** | ⚠️ Workers | ✅✅ Excellent | ✅ D1/KV | Free | Scale |

## 🎯 **Recommendation**

For SWARMZ, I'd recommend **Railway** or **Fly.io** because:
- Better Python support than Vercel
- Simpler than Render
- Built-in databases
- Better monitoring/logs
- More reliable networking

Would you like me to:
1. ✅ Commit the Render fixes (should work now)
2. 🚀 Set up Railway/Fly.io instead
3. 📝 Create migration guide for your preferred platform
