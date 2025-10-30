# Redis Setup Guide for SyroApp

## The Error You Got

```
Error syncing stats: Error 61 connecting to localhost:6379. Connection refused.
```

**Cause:** Redis is not running
**Solution:** Start Redis server

---

## Quick Fix

### Option 1: Start Redis in Background (Recommended)

```bash
# Start Redis server in the background
redis-server --daemonize yes

# Verify it's running
redis-cli ping
# Should return: PONG
```

### Option 2: Start Redis in a Separate Terminal

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2+: Run your Django app
cd /Users/angelogonzalez/Coding/SyroApp
python manage.py runserver
```

### Option 3: Using Homebrew Services

```bash
# Start Redis as a service
brew services start redis

# Stop Redis
brew services stop redis

# Verify status
brew services list
```

---

## Complete Development Setup

### Step 1: Start Redis (first, in one terminal)
```bash
redis-server --daemonize yes
```

### Step 2: Start Django in another terminal
```bash
cd /Users/angelogonzalez/Coding/SyroApp
python manage.py runserver
```

### Step 3: Start Celery (optional, in third terminal for background tasks)
```bash
cd /Users/angelogonzalez/Coding/SyroApp
celery -A Syro worker -l info
```

---

## Verification

### Check if Redis is Running
```bash
redis-cli ping
# Should return: PONG
```

### Check Redis Info
```bash
redis-cli info
# Shows detailed Redis information
```

### Check Active Connections
```bash
redis-cli client list
```

---

## What Each Component Does

### Redis
- **Purpose:** In-memory data store for caching and Celery message broker
- **Used by:** Celery (background tasks), Django caching
- **Port:** 6379 (default)
- **Start:** `redis-server`

### Django
- **Purpose:** Web application backend
- **Port:** 8000 (default)
- **Start:** `python manage.py runserver`
- **Requires:** Redis for stats syncing

### Celery
- **Purpose:** Background task processing
- **Used by:** Stats synchronization, email sending, heavy processing
- **Start:** `celery -A Syro worker -l info`
- **Requires:** Redis broker
- **Optional:** Not required for basic functionality

---

## Dependencies Between Services

```
Redis (foundation)
  ↓ (used by)
  ├─ Django (uses for caching)
  └─ Celery (uses as message broker)
```

**To sync stats, you need:**
1. Redis running ✓
2. Django running ✓
3. Celery running (optional but recommended for background tasks)

---

## Quick Troubleshooting

### Redis won't start
```bash
# Check if already running
lsof -i :6379

# Kill existing Redis process
pkill redis-server

# Try starting again
redis-server
```

### Error: "Could not connect to Redis"
```bash
# Start Redis with verbose output
redis-server --loglevel verbose

# In another terminal, test connection
redis-cli ping
```

### Stats still not syncing
1. Verify Redis is running: `redis-cli ping`
2. Verify Django is running: `curl http://localhost:8000`
3. Check Django console for errors
4. Check if Celery is running (optional)

---

## For Production

### Use supervisor or systemd
```bash
# Using systemd (Linux)
sudo systemctl start redis-server

# Using launchd (macOS)
brew services start redis
```

### Use Docker
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

---

## Understanding the Error

When you clicked "Sync Stats" on the stats page:
1. Django tried to queue a Celery task
2. Django tried to connect to Redis at localhost:6379
3. Redis wasn't running
4. Connection refused error

**Fix:** Start Redis, then try again

---

## Now Try This

### Step 1: Start Redis
```bash
redis-server --daemonize yes
redis-cli ping
# Should return: PONG
```

### Step 2: Verify Django is running
```bash
# In another terminal
curl http://localhost:8000
```

### Step 3: Go to stats page and click "Sync Stats"
- Should work now!
- You should see stats updating

---

## For Your Team

When others clone and run the project:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Django
cd SyroApp
python manage.py runserver

# Now visit http://localhost:8000 and try syncing stats
```

---

## Common Ports

| Service | Port | Status |
|---------|------|--------|
| Redis | 6379 | Should be running |
| Django | 8000 | Should be running |
| Postgres | 5432 | Only needed in production |

---

## Status Check Command

Run this to see what's running:
```bash
echo "Redis:" && redis-cli ping 2>&1 || echo "Not running"
echo "Django:" && curl http://localhost:8000 >/dev/null 2>&1 && echo "Running" || echo "Not running"
```

---

**You need Redis running for stats to work!**

Start it with: `redis-server --daemonize yes`

Then try syncing stats again.
