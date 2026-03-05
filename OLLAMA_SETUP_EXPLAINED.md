# 🔍 Important: Your Ollama Setup Explained

## Current Setup: Ollama Cloud API (No Local Installation Needed!)

### What You're Using: ☁️ Ollama Cloud API

Your CarbonTraceAI application is configured to use **Ollama Cloud API**, which means:

✅ **No local Ollama installation required**
✅ **No local Ollama service needs to run**
✅ **No GPU required on your server**
✅ **Everything runs in Ollama's cloud**

### How It Works

```
Your App (Backend)
    ↓
    → Makes HTTPS request to https://ollama.com
    → Includes API Key in Authorization header
    → Ollama Cloud processes the request
    → Returns AI response
    ↓
Your App receives result
```

### Current Configuration

**File:** `/app/backend/config.py`

```python
OLLAMA_API_KEY: str = "217a05e303fb43f691dff02adaba67f8.8QQGjpcC7VRX6RuwIvhhednF"
OLLAMA_HOST: str = "https://ollama.com"  # ← Cloud endpoint, not localhost!
VLM_MODEL: str = "kimi-k2.5:cloud"
LLM_MODEL: str = "deepseek-v3.2:cloud"
```

**Backend Code:**
```python
from ollama import Client

client = Client(
    host='https://ollama.com',  # ← Using cloud, not local
    headers={'Authorization': f'Bearer {OLLAMA_API_KEY}'}
)
```

---

## The Difference

### Option 1: Local Ollama (NOT what you're using)
```
❌ Requires installation: curl -fsSL https://ollama.com/install.sh | sh
❌ Requires local service: ollama serve
❌ Requires models download: ollama pull kimi-k2.5
❌ Uses localhost: http://localhost:11434
❌ Needs GPU for good performance
❌ You manage everything
```

### Option 2: Ollama Cloud API (WHAT YOU'RE USING ✅)
```
✅ No installation needed
✅ No service to run
✅ No models to download
✅ Uses cloud: https://ollama.com
✅ No GPU needed
✅ Ollama manages everything
✅ Just need API key
```

---

## Services Auto-Start Configuration

Your services are already configured to auto-start via **Supervisor**!

### Current Auto-Start Setup

**Supervisor Configuration Files:**

1. `/etc/supervisor/conf.d/backend.conf` - Backend auto-starts
2. `/etc/supervisor/conf.d/frontend.conf` - Frontend auto-starts

**What Auto-Starts:**
- ✅ Backend (FastAPI on port 8001)
- ✅ Frontend (React on port 3000)
- ✅ MongoDB (Database on port 27017)

**What DOESN'T Need to Auto-Start:**
- ❌ Local Ollama (you're using cloud API!)

### Service Status

Check with:
```bash
sudo supervisorctl status
```

Current status:
```
backend    RUNNING   ✅
frontend   RUNNING   ✅
mongodb    RUNNING   ✅
```

---

## If You Ever Need Local Ollama (You Don't Currently)

If in the future you want to switch to local Ollama:

### Step 1: Install Ollama
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### Step 2: Create Supervisor Config
```bash
sudo nano /etc/supervisor/conf.d/ollama.conf
```

Content:
```ini
[program:ollama]
command=/usr/local/bin/ollama serve
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/ollama.err.log
stdout_logfile=/var/log/supervisor/ollama.out.log
environment=OLLAMA_HOST=0.0.0.0:11434
```

### Step 3: Update Backend Config
```python
OLLAMA_HOST: str = "http://localhost:11434"  # Change from https://ollama.com
# Remove API key (not needed for local)
```

### Step 4: Pull Models
```bash
ollama pull kimi-k2.5
ollama pull deepseek-v3.2
```

**But again, you DON'T need this with your current cloud setup!**

---

## Troubleshooting Parsing Issues

If parsing isn't working after agent sleep:

### 1. Check Services
```bash
sudo supervisorctl status
```

If any service is stopped:
```bash
sudo supervisorctl restart all
```

### 2. Check Backend Logs
```bash
tail -n 50 /var/log/supervisor/backend.err.log
```

### 3. Test Ollama Cloud API
```bash
curl https://ollama.com/api/tags \
  -H "Authorization: Bearer 217a05e303fb43f691dff02adaba67f8.8QQGjpcC7VRX6RuwIvhhednF"
```

### 4. Check Frontend Connection
Visit: https://f234f04a-ce0d-43b6-9cfe-74f80c24c0b1.preview.emergentagent.com

### 5. Restart Everything
```bash
sudo supervisorctl restart all
```

---

## Summary

**You DON'T need to run local Ollama!**

Your setup is:
```
CarbonTraceAI Backend → Ollama Cloud API → AI Processing → Response
                     (via HTTPS with API key)
```

Everything you need is already auto-starting:
- ✅ Backend (with Ollama Cloud API client)
- ✅ Frontend
- ✅ MongoDB

If parsing stops working, it's likely because:
1. Backend service stopped (restart with `sudo supervisorctl restart backend`)
2. Network issue (check internet connection)
3. API key issue (verify key is still valid)
4. Session expired (re-login to app)

**NOT because local Ollama isn't running (you're not using local Ollama!)**

---

## Quick Commands Reference

**Check all services:**
```bash
sudo supervisorctl status
```

**Restart all services:**
```bash
sudo supervisorctl restart all
```

**Check backend logs:**
```bash
tail -f /var/log/supervisor/backend.err.log
```

**Test Ollama Cloud API:**
```bash
python3 -c "from ollama import Client; client = Client(host='https://ollama.com', headers={'Authorization': 'Bearer 217a05e303fb43f691dff02adaba67f8.8QQGjpcC7VRX6RuwIvhhednF'}); print(client.chat(model='kimi-k2.5:cloud', messages=[{'role': 'user', 'content': 'test'}])['message']['content'])"
```

**Test backend health:**
```bash
curl http://localhost:8001/api/health
```

---

**Last Updated:** March 5, 2026
**Configuration:** Ollama Cloud API (No local installation)
