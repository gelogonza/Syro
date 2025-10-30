# SyroApp - Music Player Application

A modern, feature-rich music player web application that integrates with Spotify to provide a seamless listening experience with advanced playlist management, real-time search, and personalized statistics.

## Overview

SyroApp is a Django-based web application that connects to Spotify's Web Playback SDK, allowing users to browse, search, and play music directly through a beautiful dark-themed interface. The application provides comprehensive music management features including playlist creation, artist browsing, album exploration, and listening statistics.

## Key Features

### Core Music Features
- **Spotify Integration**: Connect your Spotify account and control playback directly through the app
- **Web Playback**: Play music through Spotify Web Playback SDK on any device
- **Device Selection**: Choose which device to play music on (computer, phone, speakers, etc.)
- **Playlist Management**: Create, edit, and delete custom playlists
- **Smart Search**: Real-time search across songs, artists, and albums with hybrid local/Spotify search

### Visual Features
- **Vinyl Record Animation**: Beautiful animated vinyl record that spins during playback
- **Dynamic Backgrounds**: Player background changes colors based on album artwork using Canvas API
- **Dark Theme**: Professional dark interface optimized for viewing comfort and reduced eye strain
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **Frosted Glass Navigation**: Modern UI with glass-morphism effects
- **Gradient Backgrounds**: Animated gradients on home page and key pages

### Music Discovery & Management
- **Browse Artists**: Explore artist profiles and discographies
- **Album Details**: View album information with complete tracklists
- **Song Management**: Add songs to playlists, view track details
- **Genre Browsing**: Discover music by genre
- **Recommendations**: Get music recommendations based on your listening

### Statistics & Analytics
- **Listening Statistics**: Track your listening habits and favorite artists
- **Wrapped Feature**: Annual summary of your listening history
- **User Activity Tracking**: Monitor your music discovery journey
- **Detailed Analytics**: View play counts, listening trends, and more

### Advanced Search Capabilities
- **Player Search**: Search and play songs directly from the player
- **Playlist Search**: Search and add songs to playlists in real-time
- **Hybrid Search**: Combines local database with Spotify API results
- **Debounced Input**: Optimized search with 300ms debounce for performance
- **Song Results with Metadata**: Full artist and album information

## Technical Stack

### Backend
- **Framework**: Django 5.0
- **Database**: SQLite (with PostgreSQL support for production)
- **Authentication**: Spotify OAuth 2.0
- **API Integration**: Spotipy (Spotify Web API client)
- **Task Queue**: Celery (optional for background tasks)

### Frontend
- **HTML/CSS/JavaScript**: Vanilla implementation
- **Styling**: Tailwind CSS with custom dark theme
- **Icons**: Iconify icon library
- **Fonts**: Inter font family
- **Animation**: CSS animations and Canvas API for color extraction
- **Real-time Updates**: AJAX for dynamic content loading

## Installation & Setup

### Prerequisites
- Python 3.8+
- pip and virtualenv
- Spotify Developer Account

### Step-by-Step Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd SyroApp
```

2. **Create and activate virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up Spotify Developer Credentials**
- Visit https://developer.spotify.com/dashboard
- Create a new application
- Note your Client ID and Client Secret
- Set Redirect URI to http://localhost:8000/music/spotify/callback/

5. **Configure environment variables**
Create a `.env` file in the project root:
```bash
SPOTIPY_CLIENT_ID=your_client_id_here
SPOTIPY_CLIENT_SECRET=your_client_secret_here
SPOTIPY_REDIRECT_URI=http://localhost:8000/music/spotify/callback/
DJANGO_SECRET_KEY=your_secret_key_here
DEBUG=True
```

6. **Run database migrations**
```bash
python manage.py migrate
```

7. **Create admin user (optional)**
```bash
python manage.py createsuperuser
```

8. **Start the development server**
```bash
python manage.py runserver
```

9. **Access the application**
Open http://localhost:8000 in your browser

## Project Structure

```
SyroApp/
├── Syro/                          # Django project settings
│   ├── settings.py                # Project configuration
│   ├── urls.py                    # Main URL routing
│   └── wsgi.py                    # WSGI configuration
│
├── SyroMusic/                     # Main application
│   ├── models.py                  # Database models
│   ├── views.py                   # View logic
│   ├── urls.py                    # App URL routing
│   ├── admin.py                   # Django admin config
│   ├── search_views.py            # Search API endpoints
│   ├── playback_views.py          # Playback control
│   │
│   ├── migrations/                # Database migrations
│   │
│   └── templates/                 # HTML templates
│       ├── base.html              # Base template
│       └── syromusic/             # Page templates
│           ├── home.html
│           ├── player.html
│           ├── playlist_list.html
│           ├── search.html
│           └── ... (other pages)
│
├── manage.py                      # Django CLI
├── requirements.txt               # Dependencies
├── .env                           # Environment variables (not in git)
├── .gitignore                     # Git rules
└── README.md                      # This file
```

## Core API Endpoints

### Authentication
- `GET /music/spotify/login/` - Initiate Spotify OAuth
- `GET /music/spotify/callback/` - OAuth callback

### Music Management
- `GET /music/songs/` - List songs
- `GET /music/albums/` - List albums
- `GET /music/artists/` - List artists
- `GET /music/playlists/` - User playlists

### Search
- `GET /music/api/search/?q=query` - Smart search

### Playback
- `POST /music/api/play/` - Play track
- `POST /music/api/pause/` - Pause
- `POST /music/api/next/` - Next track
- `POST /music/api/previous/` - Previous track
- `GET /music/api/devices/` - Get devices

### Statistics
- `GET /music/stats/` - Listening statistics
- `GET /music/wrapped/` - Annual wrapped

## Usage Guide

### Getting Started
1. Navigate to http://localhost:8000
2. Click "Connect with Spotify"
3. Login with your Spotify account
4. Grant permissions
5. Start using SyroApp

### Playing Music
1. Go to Player page
2. Search for songs
3. Click play button
4. Select device if prompted
5. Use controls to manage playback

### Creating Playlists
1. Navigate to Playlists
2. Click "Create New Playlist"
3. Enter name and description
4. Add songs via search feature
5. Manage songs in playlist

### Viewing Statistics
- **Dashboard**: Overview of listening activity
- **Stats Page**: Detailed statistics and trends
- **Wrapped**: Annual listening summary

## Configuration Details

### Tailwind CSS Theme
Custom dark theme configuration in `base.html`:
- Background: #0a0a0a (pure black)
- Cards: #1a1a1a (very dark gray)
- Text: #ffffff (white)
- Accents: #10b981 (emerald green)

### Spotify OAuth Settings
Configured in `settings.py`:
- Uses environment variables for credentials
- Secure token storage
- Required scopes for playback

## Performance Optimizations

### Implemented
- Search debouncing (300ms)
- Lazy loading for lists
- GPU-accelerated CSS animations
- Optimized color extraction
- Efficient database queries

### Best Practices
- Minimize HTTP requests
- Use AJAX for dynamic updates
- Optimize images
- Cache frequently accessed data
- Use CDN for static assets

## Security Features

### Implemented Measures
- CSRF protection on all forms
- Secure OAuth token handling
- Input validation and sanitization
- XSS prevention via template escaping
- No sensitive data in client code

### Environment Security
Keep in `.env` (never commit):
- SPOTIPY_CLIENT_ID
- SPOTIPY_CLIENT_SECRET
- DJANGO_SECRET_KEY
- Database credentials

## Browser Compatibility

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile Chrome
- Mobile Safari

## Troubleshooting

### Spotify Connection Issues
1. Verify credentials in .env
2. Check Redirect URI matches exactly
3. Ensure account has Web Playback permission

### Playback Problems
1. Verify active device in Spotify
2. Refresh device list
3. Check browser console for errors

### Search Not Working
1. Verify API credentials
2. Check network requests in DevTools
3. Ensure query is 2+ characters

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Admin Panel
Access at `/admin/` with superuser credentials

## Future Enhancement Ideas

Potential features:
- Theme switching (light/dark toggle)
- Local MP3 file uploads
- Queue management
- Lyrics display with sync
- Social sharing features
- Advanced recommendations
- Podcast support
- High-resolution audio
- Offline playback

## Contributing

Guidelines:
- Follow project style guide
- Ensure all tests pass
- Maintain security standards
- Update documentation
- Do not commit sensitive data

## Support & Documentation

For help:
1. Check troubleshooting section
2. Review browser console errors
3. Verify Spotify setup
4. Check .env configuration

## License

Educational and personal use.

## Acknowledgments

Built with:
- Django
- Spotify Web API
- Tailwind CSS
- Iconify
- Inter Font

---

**Version**: 1.0
**Last Updated**: October 29, 2025
**Status**: Production Ready
