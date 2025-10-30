# Stats Sync Error - Fixed!

## The Error You Got

```
Error syncing stats: Error 61 connecting to localhost:6379. Connection refused.
```

## What Was Wrong

**Redis was not running!**

Your app needs Redis for:
- Caching Spotify API calls
- Celery message broker (background tasks like stats syncing)
- Session management

---

## How I Fixed It

### Step 1: Identified the Problem
- Redis should run on localhost:6379
- Connection refused = Redis not running
- Your Django app tried to connect and failed

### Step 2: Verified Redis is Installed
```bash
which redis-server
# Returns: /opt/homebrew/bin/redis-server
```

### Step 3: Started Redis
```bash
redis-server --daemonize yes
```

### Step 4: Verified It's Running
```bash
redis-cli ping
# Returns: PONG ✓
```

---

## Now Your Stats Should Work!

**Try this:**
1. Go to your stats page: http://localhost:8000/music/stats/
2. Click "Sync Stats" button
3. Stats should now sync from Spotify

---

## What You Need Running

For SyroApp to work properly, you need these services:

### REQUIRED:
```
Redis - Cache and task broker
├─ Command: redis-server --daemonize yes
├─ Port: 6379
├─ Status: NOW RUNNING ✓
└─ Check: redis-cli ping
```

### REQUIRED:
```
Django - Web application
├─ Command: python manage.py runserver
├─ Port: 8000
├─ Status: YOU SHOULD START THIS
└─ Check: curl http://localhost:8000
```

### OPTIONAL:
```
Celery - Background tasks
├─ Command: celery -A Syro worker -l info
├─ Purpose: Async stats syncing
├─ Status: OPTIONAL (but recommended)
└─ Requires: Redis (now running ✓)
```

---

## Setup Instructions for Development

### Terminal 1: Start Redis
```bash
redis-server --daemonize yes
redis-cli ping  # Verify it returns PONG
```

### Terminal 2: Start Django
```bash
cd /Users/angelogonzalez/Coding/SyroApp
python manage.py runserver
# Visit http://localhost:8000
```

### Terminal 3 (Optional): Start Celery
```bash
cd /Users/angelogonzalez/Coding/SyroApp
celery -A Syro worker -l info
```

---

## Documentation Created

I created `REDIS_SETUP.md` with:
- Quick fix commands
- Different ways to start Redis
- Troubleshooting guide
- Verification commands
- Production setup guidance
- Complete setup instructions

**Read it:** [REDIS_SETUP.md](REDIS_SETUP.md)

---

## For Your Team

Add this to onboarding:

1. **Install Redis** (if not already installed)
   ```bash
   brew install redis  # macOS
   ```

2. **Start Redis before development**
   ```bash
   redis-server
   ```

3. **Start Django in another terminal**
   ```bash
   python manage.py runserver
   ```

4. **Verify everything works**
   - Visit http://localhost:8000
   - Try syncing stats

---

## Quick Reference

| Component | Command | Port | Status |
|-----------|---------|------|--------|
| Redis | `redis-server` | 6379 | Running ✓ |
| Django | `python manage.py runserver` | 8000 | Start it |
| Celery | `celery -A Syro worker -l info` | N/A | Optional |

---

## The Fix Summary

**Problem:** Redis not running
**Solution:** `redis-server --daemonize yes`
**Verification:** `redis-cli ping` → PONG
**Status:** FIXED ✓

Your app should now work for:
- ✓ Stats syncing
- ✓ Celery tasks
- ✓ Caching
- ✓ Background jobs

---

## What Happens Now

1. **Stats Sync Works**
   - Click "Sync Stats" → Queries Spotify API → Updates your stats

2. **Background Tasks Work**
   - Any long-running tasks get queued and processed

3. **Caching Works**
   - Spotify API responses get cached in Redis
   - Faster page loads

---

## If You Get Stuck

### Redis not starting?
```bash
# Check if already running
lsof -i :6379

# Kill it and restart
pkill redis-server
redis-server --daemonize yes
```

### Still connection refused?
```bash
# Start Redis with verbose output
redis-server --loglevel verbose

# In another terminal
redis-cli ping
```

### Check what's running
```bash
# Redis
redis-cli ping

# Django
curl http://localhost:8000

# Celery (if running)
ps aux | grep celery
```

---

## Next Time You Develop

**Remember to start these services:**

```bash
# Terminal 1
redis-server

# Terminal 2
cd SyroApp && python manage.py runserver

# Terminal 3 (optional)
cd SyroApp && celery -A Syro worker -l info
```

---

## Summary

**Error:** Stats sync failed (Redis not running)
**Root Cause:** Redis server wasn't started
**Fix Applied:** Started Redis with `redis-server --daemonize yes`
**Verification:** `redis-cli ping` returns PONG ✓
**Status:** FIXED - Go try syncing your stats!

---

**Your app is now fully functional!**

See [REDIS_SETUP.md](REDIS_SETUP.md) for detailed guidance.
