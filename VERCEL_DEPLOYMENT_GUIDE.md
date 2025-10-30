# Vercel Deployment Guide for SyroMusic (Django)

**Last Updated**: October 30, 2025

---

## Overview

This guide explains how to deploy your SyroMusic Django application to Vercel. Vercel supports Python/Django applications through Serverless Functions.

**Note**: Vercel has limitations for Django apps:
- No persistent filesystem (database must be external)
- Cold starts on serverless functions
- Long-running tasks not ideal
- Better for APIs + static frontends

---

## Option 1: Full Django on Vercel (Recommended Setup)

### Prerequisites

1. **Vercel Account**: https://vercel.com
2. **GitHub Repository**: https://github.com/gelogonza/Syro (already set up ✅)
3. **External Database**: PostgreSQL (Vercel doesn't support SQLite in serverless)
4. **AWS S3 or Similar**: For media/static files
5. **Environment Variables**: Configured in Vercel

### Step 1: Set Up External PostgreSQL Database

#### Option A: Using Vercel Postgres (Easiest)

```bash
# In Vercel dashboard:
# 1. Go to your project settings
# 2. Click "Storage" tab
# 3. Click "Create Database" → "Postgres"
# 4. Follow prompts to create database
# 5. Copy connection string
```

#### Option B: Using AWS RDS/Digital Ocean PostgreSQL

```bash
# Get connection string from your provider
# Format: postgresql://user:password@host:port/dbname
```

### Step 2: Create vercel.json Configuration

Create `vercel.json` in your project root:

```json
{
  "buildCommand": "pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput",
  "env": {
    "DJANGO_SETTINGS_MODULE": "Syro.settings"
  },
  "functions": {
    "Syro/wsgi.py": {
      "memory": 3008,
      "maxDuration": 60
    }
  },
  "routes": [
    {
      "src": "/static/(.*)",
      "dest": "/static/$1",
      "headers": {
        "cache-control": "public, max-age=31536000, immutable"
      }
    },
    {
      "src": "/(.*)",
      "dest": "/Syro/wsgi.py"
    }
  ]
}
```

### Step 3: Update requirements.txt

Ensure these are included:

```txt
Django==5.0.2
djangorestframework==3.14.0
django-cors-headers==4.0.0
django-filter==23.1
django-celery-results==2.5.0
spotipy==2.22.1
python-decouple==3.8
psycopg2-binary==2.9.9
django-storages==1.14.2
boto3==1.28.68
whitenoise==6.5.0
gunicorn==21.2.0
redis==5.0.0
django-redis==5.3.0
Pillow==10.0.0
```

### Step 4: Update settings.py for Production

Add/modify these settings:

```python
# settings.py

# Vercel deployment
import os
from decouple import config

# Set DEBUG based on environment
DEBUG = config('DJANGO_DEBUG', default=False, cast=bool)

# Allow Vercel domain
ALLOWED_HOSTS = config('DJANGO_ALLOWED_HOSTS', default='localhost,127.0.0.1').split(',')

# Database - Use PostgreSQL in production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DATABASE_NAME', default=''),
        'USER': config('DATABASE_USER', default=''),
        'PASSWORD': config('DATABASE_PASSWORD', default=''),
        'HOST': config('DATABASE_HOST', default=''),
        'PORT': config('DATABASE_PORT', default='5432'),
    }
}

# Static files - Use S3 or Vercel Blob
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# For S3 storage (optional)
if not DEBUG:
    STORAGES = {
        'default': {
            'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
            'OPTIONS': {
                'AWS_ACCESS_KEY_ID': config('AWS_ACCESS_KEY_ID'),
                'AWS_SECRET_ACCESS_KEY': config('AWS_SECRET_ACCESS_KEY'),
                'AWS_STORAGE_BUCKET_NAME': config('AWS_STORAGE_BUCKET_NAME'),
                'AWS_S3_REGION_NAME': config('AWS_S3_REGION_NAME', default='us-east-1'),
            }
        }
    }

# Enable security features in production
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='https://*.vercel.app,https://*.yourdomain.com'
).split(',')

# Logging for Vercel
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

### Step 5: Environment Variables in Vercel

In Vercel Dashboard → Project Settings → Environment Variables:

```
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ENV=production
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,*.vercel.app

# Database (from Vercel Postgres)
DATABASE_URL=postgresql://user:password@host:5432/dbname
DATABASE_NAME=dbname
DATABASE_USER=user
DATABASE_PASSWORD=password
DATABASE_HOST=host
DATABASE_PORT=5432

# Spotify
SPOTIPY_CLIENT_ID=your-spotify-client-id
SPOTIPY_CLIENT_SECRET=your-spotify-client-secret
SPOTIPY_REDIRECT_URI=https://yourdomain.com/music/spotify/callback/

# CORS
CORS_ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# AWS S3 (if using S3)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-east-1

# Cache (optional - use Redis)
REDIS_URL=redis://user:password@host:port

# Security
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://*.vercel.app
```

### Step 6: Create vercel.json (API Routes)

Alternative approach using Vercel API routes:

```json
{
  "buildCommand": "pip install -r requirements.txt",
  "env": {
    "PYTHONUNBUFFERED": "true"
  },
  "functions": {
    "api/**/*.py": {
      "runtime": "python3.11"
    }
  }
}
```

### Step 7: Deploy to Vercel

#### Option A: GitHub Integration (Easiest)

```bash
# 1. Push code to GitHub
git push origin main

# 2. In Vercel Dashboard:
# - Click "New Project"
# - Select GitHub repository (Syro)
# - Vercel auto-detects Django
# - Add environment variables
# - Click "Deploy"
```

#### Option B: Vercel CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy from command line
vercel

# Link to GitHub project when prompted
# Set environment variables in Vercel dashboard
```

### Step 8: Run Initial Migrations

After first deployment:

```bash
# Via Vercel environment
vercel env pull  # Pull environment variables

# Run migrations
python manage.py migrate --settings=Syro.settings
```

---

## Option 2: Hybrid Approach (Recommended for Django)

**Frontend**: Vercel (Next.js/React)
**Backend**: Heroku or Railway (Django)

### Why Hybrid?

- ✅ Django works better on traditional servers
- ✅ Easier database/file management
- ✅ Better for long-running tasks
- ✅ Easier caching with Redis
- ✅ Less cold start issues

### Setup

#### Frontend (Vercel)

```bash
# Create Next.js app for frontend
npx create-next-app@latest frontend

# Deploy to Vercel
vercel
```

#### Backend (Heroku/Railway)

```bash
# Deploy Django separately to Heroku
# See: https://devcenter.heroku.com/articles/getting-started-with-python

# Or use Railway.app (easier):
# https://railway.app/
```

#### Connect Frontend to Backend

```javascript
// In Next.js frontend
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

fetch(`${API_URL}/music/api/artists/`)
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## Option 3: Docker + Vercel

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "Syro.wsgi:application", "--bind", "0.0.0.0:8000"]
```

Deploy via Vercel with Docker support (Enterprise feature).

---

## Recommended: Railway.app (Easier for Django)

Railway.app is better for Django apps than Vercel:

### Step 1: Create Railway Account

https://railway.app/

### Step 2: Create New Project

```bash
# Click "New Project" → "Deploy from GitHub"
# Select your Syro repository
```

### Step 3: Add PostgreSQL Database

```bash
# In Railway dashboard:
# Click "Add" → "PostgreSQL"
# It creates DATABASE_URL automatically
```

### Step 4: Set Environment Variables

```bash
# In Railway dashboard → Variables tab:
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
SPOTIPY_CLIENT_ID=your-id
SPOTIPY_CLIENT_SECRET=your-secret
SPOTIPY_REDIRECT_URI=https://yourdomain.railway.app/music/spotify/callback/
```

### Step 5: Deploy

```bash
# Push to GitHub
git push origin main

# Railway auto-deploys!
# No additional configuration needed
```

---

## Post-Deployment Checklist

### Verification

- [ ] Website loads without errors
- [ ] Static files served correctly (CSS/JS working)
- [ ] Database migrations applied
- [ ] Spotify auth working
- [ ] API endpoints responding
- [ ] Admin panel accessible

### Performance

- [ ] Page load time < 3 seconds
- [ ] No 500 errors in logs
- [ ] Cache working
- [ ] Rate limiting active

### Security

- [ ] HTTPS enforced
- [ ] CSRF tokens working
- [ ] Environment variables not exposed
- [ ] No debug mode in production
- [ ] CORS configured correctly

### Monitoring

- [ ] Error logs monitored
- [ ] Performance metrics tracked
- [ ] Uptime monitoring enabled
- [ ] Email alerts configured

---

## Troubleshooting

### Issue: Database Connection Failed

```bash
# Check environment variables
vercel env list

# Verify DATABASE_URL format:
# postgresql://user:password@host:port/dbname

# Test connection:
python manage.py shell
```

### Issue: Static Files Not Serving

```bash
# Run collectstatic
python manage.py collectstatic --noinput

# Check STATIC_ROOT in settings.py
# Ensure S3 credentials if using S3
```

### Issue: Cold Starts Slow

**Solutions**:
- Use Railway.app instead (warm instances)
- Upgrade Vercel Pro for more memory
- Use API caching to reduce DB queries
- Implement request batching

### Issue: Spotify OAuth Not Working

```python
# Verify SPOTIPY_REDIRECT_URI matches:
# 1. Environment variable
# 2. Spotify app dashboard
# 3. Django ALLOWED_HOSTS

# Format: https://yourdomain.com/music/spotify/callback/
```

### Issue: Media Files Not Saving

**Solutions**:
- Use S3 for media storage (recommended)
- Use Vercel Blob for file storage
- Configure `django-storages` properly

---

## Comparison: Hosting Options

| Platform | Setup | Django | Database | Cost | Cold Start |
|----------|-------|--------|----------|------|-----------|
| **Vercel** | Easy | OK | External | Free tier | Slow |
| **Railway** | Easy | Great | Built-in | Pay-per-use | Fast |
| **Heroku** | Moderate | Great | Built-in | $7+/month | Fast |
| **PythonAnywhere** | Easy | Great | Built-in | Free tier | N/A |
| **AWS EC2** | Hard | Great | Any | Variable | N/A |

**Recommendation for SyroMusic**: **Railway.app** or **Heroku** (both better than Vercel for Django)

---

## Quick Start: Railway Deployment

```bash
# 1. Create Railway account
# https://railway.app/

# 2. Install Railway CLI
npm i -g @railway/cli

# 3. Login to Railway
railway login

# 4. Create project
railway init

# 5. Add database
railway add

# 6. Deploy
railway up

# 7. Open deployed app
railway open
```

Done! Your Django app is live on Railway.

---

## Production Checklist

Before deploying to production:

- [ ] SECRET_KEY is production-grade (50+ chars, random)
- [ ] DEBUG = False in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] HTTPS/SSL enabled
- [ ] Database backups configured
- [ ] Static files serving correctly
- [ ] Media files storage configured
- [ ] Email sending configured (SMTP)
- [ ] Error logging configured
- [ ] Performance optimizations applied
- [ ] Security headers enabled
- [ ] CORS configured for frontend domain

---

## Conclusion

**Best Option for SyroMusic Django App**:

1. **First Choice**: Railway.app (easiest, best for Django)
2. **Second Choice**: Heroku (reliable, proven)
3. **Third Choice**: Vercel (possible, but not ideal for Django)

**Avoid**: Vercel for traditional Django apps - use Railway or Heroku instead.

---

For questions or issues, refer to:
- [Django Deployment Docs](https://docs.djangoproject.com/en/5.0/howto/deployment/)
- [Railway Docs](https://docs.railway.app/)
- [Vercel Docs](https://vercel.com/docs)

