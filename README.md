# Syro - Spotify Music Streaming Application

A full-featured Django-based music streaming application that integrates with Spotify API, allowing users to manage playlists, track listening statistics, discover recommendations, and control music playback.

## Features

### Core Features
- **Spotify OAuth Authentication**: Secure login using Spotify account
- **Music Playback**: Control music playback with device selection and playback controls
- **Playlist Management**: Create, edit, delete, and manage personal playlists
- **Artist & Album Browsing**: Explore artists and albums with detailed information
- **Song Details**: View detailed information about songs including duration and track number
- **Search Functionality**: Search for artists, albums, tracks, and playlists
- **Music Discovery**: 
  - Browse music by genre
  - Get personalized recommendations based on listening history
  - Discover top artists and tracks

### Statistics & Analytics
- **Listening Statistics Dashboard**: View listening statistics including:
  - Top artists (short, medium, and long-term)
  - Top tracks (short, medium, and long-term)
  - Total artists followed
  - Total playlists and saved tracks
  - Favorite genres
  - Recently played tracks

### Playback Controls
- Play/Pause toggle
- Next/Previous track
- Shuffle and Repeat modes
- Volume control
- Progress bar with seek functionality
- Device selection and playback transfer
- Queue management

## Tech Stack

### Backend
- **Framework**: Django 5.0.2
- **Database**: SQLite (development) / PostgreSQL (recommended for production)
- **Authentication**: Spotify OAuth 2.0
- **API Integration**: Spotipy (Python Spotify Web API wrapper)
- **Task Queue**: Celery with Redis
- **REST API**: Django REST Framework

### Frontend
- **Template Engine**: Django Templates
- **Styling**: CSS3 with responsive design
- **JavaScript**: Vanilla JavaScript for interactive features

### Key Dependencies
```
Django==5.0.2
djangorestframework==3.14.0
django-cors-headers==4.0.0
django-filter==23.1
spotipy==2.22.1
celery==5.2.7
redis==4.5.5
python-decouple==3.8
cryptography==40.0.1
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip and virtualenv
- Redis server (for Celery tasks)
- Spotify Developer Account (for OAuth credentials)

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd SyroApp
```

### Step 2: Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables
Create a `.env` file in the project root:
```bash
# Django Settings
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False
DJANGO_ENV=production
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Spotify Configuration
SPOTIPY_CLIENT_ID=your-spotify-client-id
SPOTIPY_CLIENT_SECRET=your-spotify-client-secret
SPOTIPY_REDIRECT_URI=http://localhost:8000/music/spotify/callback/

# Database (optional for production)
DATABASE_URL=postgresql://user:password@localhost/syro

# Redis Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

### Step 5: Run Migrations
```bash
python manage.py migrate
```

### Step 6: Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### Step 7: Start Development Server
```bash
python manage.py runserver
```

### Step 8: Start Celery (In another terminal)
```bash
celery -A Syro worker -l info
```

### Step 9: Start Celery Beat (In another terminal, optional for scheduled tasks)
```bash
celery -A Syro beat -l info
```

## API Endpoints

### Authentication
- `GET /music/` - Home page
- `POST /auth/signup/` - User registration
- `POST /auth/login/` - User login
- `GET /music/spotify/login/` - Spotify OAuth login
- `GET /music/spotify/callback/` - OAuth callback

### Music Browser
- `GET /music/artists/` - List all artists
- `GET /music/artists/<id>/` - Artist details
- `GET /music/albums/` - List all albums
- `GET /music/albums/<id>/` - Album details
- `GET /music/songs/` - List all songs
- `GET /music/songs/<id>/` - Song details
- `GET /music/playlists/` - List user playlists
- `GET /music/playlists/<id>/` - Playlist details

### Playback & Control
- `POST /api/v1/playback/play/` - Start playback
- `POST /api/v1/playback/pause/` - Pause playback
- `POST /api/v1/playback/next/` - Next track
- `POST /api/v1/playback/previous/` - Previous track
- `POST /api/v1/playback/seek/` - Seek to position
- `POST /api/v1/playback/set-volume/` - Set volume
- `POST /api/v1/playback/set-shuffle/` - Toggle shuffle
- `POST /api/v1/playback/set-repeat/` - Set repeat mode

### Playlists
- `POST /music/playlists/create/` - Create playlist
- `POST /music/playlists/<id>/update/` - Update playlist
- `POST /music/playlists/<id>/delete/` - Delete playlist
- `POST /music/playlists/add-song/` - Add song to playlist
- `POST /music/playlists/remove-song/` - Remove song from playlist

### Search & Discovery
- `GET /music/search/` - Search with query parameter `?q=<query>`
- `GET /music/recommendations/` - Get personalized recommendations
- `GET /music/browse-genres/` - Browse music by genre
- `POST /music/save-track/<id>/` - Save/like a track
- `POST /music/unsave-track/<id>/` - Remove from saved tracks

### Statistics
- `GET /music/stats-dashboard/` - User's statistics dashboard
- `GET /api/v1/stats/top-artists/<period>/` - Top artists (short_term/medium_term/long_term)
- `GET /api/v1/stats/top-tracks/<period>/` - Top tracks
- `GET /api/v1/stats/listening-activity/` - Listening activity history

## Security Features

### Implemented Security Measures
1. **Token Encryption**: All Spotify access tokens are encrypted using Fernet encryption
2. **Environment Variables**: Sensitive configuration stored in `.env` files (not in version control)
3. **CSRF Protection**: CSRF tokens required for all form submissions
4. **Secure Cookies**: 
   - HTTPOnly flag for session cookies
   - Secure flag enabled in production
5. **SQL Injection Prevention**: Django ORM parameterized queries
6. **XSS Protection**: Template auto-escaping enabled
7. **CORS**: Restricted to whitelisted domains
8. **Authentication**: Spotify OAuth 2.0 with token refresh mechanism

### Production Security Checklist
- [ ] Set `DEBUG = False`
- [ ] Set a strong `SECRET_KEY` in environment
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Enable `SECURE_SSL_REDIRECT = True`
- [ ] Set `SESSION_COOKIE_SECURE = True`
- [ ] Configure PostgreSQL for production database
- [ ] Set up proper logging and monitoring
- [ ] Use HTTPS with valid SSL certificate
- [ ] Enable Django security middleware
- [ ] Configure proper CORS settings

## Deployment Guide

### Deploying to Production

#### Option 1: Heroku
```bash
# Install Heroku CLI
# Create Procfile
web: gunicorn Syro.wsgi --log-file -

# Create requirements.txt
pip freeze > requirements.txt

# Deploy
heroku create your-app-name
heroku addons:create heroku-postgresql:hobby-dev
heroku config:set DJANGO_SECRET_KEY=your-secret-key
git push heroku main
heroku run python manage.py migrate
```

#### Option 2: AWS/DigitalOcean
```bash
# Install gunicorn
pip install gunicorn

# Install nginx
sudo apt-get install nginx

# Configure supervisor for process management
sudo apt-get install supervisor

# Create static files
python manage.py collectstatic --noinput

# Start with gunicorn
gunicorn Syro.wsgi:application --bind 0.0.0.0:8000
```

#### Option 3: Docker
Create a `Dockerfile`:
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "Syro.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Performance Optimization Tips

1. **Database**: Use PostgreSQL for production
2. **Caching**: Implement Redis caching for frequently accessed data
3. **Pagination**: API endpoints use pagination (20 items per page)
4. **Lazy Loading**: Images load only when needed
5. **Task Queue**: Use Celery for background syncing of listening statistics
6. **Database Indexes**: Added indexes on frequently queried fields

## Troubleshooting

### Spotify Token Expiration
Tokens are automatically refreshed when they expire. If you encounter "Invalid access token" errors:
1. Re-authenticate with Spotify
2. Check token expiration in the admin panel

### Playback Issues
- Ensure Spotify app is running on at least one device
- Check device connectivity
- Verify Spotify Premium account (required for playback)

### Database Errors
- Clear cache: `python manage.py flush`
- Reset migrations: Remove migration files and run `python manage.py makemigrations && python manage.py migrate`

### Redis Connection Issues
- Ensure Redis server is running: `redis-cli ping`
- Check Redis connection in settings.py

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, email support@syro.com or open an issue in the GitHub repository.

## Acknowledgments

- Spotify Web API for music data
- Django framework for robust backend
- All contributors and testers

---

**Note**: Remember to replace placeholder values like `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` with your actual Spotify API credentials before running the application.
