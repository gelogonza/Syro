# SyroApp - Intelligent Music Discovery Platform

A sophisticated, feature-rich music discovery and playback application that integrates with Spotify to provide an intelligent listening experience with advanced playlist management, real-time search, color-based discovery, personalized insights, and AI-like music recommendations.

## Overview

SyroApp is a premium Django-based web application that combines music playback, discovery, and analytics into a unified platform. It connects to Spotify's Web Playback SDK while adding layers of intelligent discovery through color psychology, audio feature analysis, and mood-based recommendations. The application provides comprehensive music management features including playlist creation, artist browsing, album exploration, listening statistics, color-based discovery, shareable vibe receipts, and smart randomized music discovery.

## Key Features

### Core Music Features
- **Spotify Integration**: Connect your Spotify account and control playback directly through the app
- **Web Playback**: Play music through Spotify Web Playback SDK on any device
- **Device Selection**: Choose which device to play music on (computer, phone, speakers, etc.)
- **Playlist Management**: Create, edit, and delete custom playlists
- **Smart Search**: Real-time search across songs, artists, and albums with hybrid local/Spotify search

### Premium Visual Features (Phase 1: "The Deck")
- **Vinyl Record Animation**: Beautiful animated vinyl record with grooves that spins during playback
- **Breathing Animation**: 8-second pulsing gradient with scale effect for premium feel
- **Premium Typography**: Large bold titles with gradient text effects
- **Grain Overlay**: SVG-based noise for analog/archival aesthetic
- **Dynamic Backgrounds**: Radial gradients responding to track mood with smooth transitions
- **Enhanced Controls**: Premium button styling with hover states and elevation effects
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

### Color-Based Discovery (Phase 2: "The Crate")
- **Album Color Extraction**: Intelligent PIL-based color quantization extracts dominant colors from album artwork
- **Color-Based Filtering**: Filter albums by dominant color with visual palette selector
- **Masonry Grid Layout**: Responsive grid with hover-reveal album metadata
- **Color Palette Discovery**: See all available colors in your library with album counts
- **Automated Color Processing**: Celery background task automatically extracts colors from new albums
- **Performance Optimized**: Database indexing and efficient queries for instant filtering

### Personalized Insights (Phase 3: "Sonic Aura")
- **Vibe Score**: Algorithmic personality score (0-100) based on last 50 tracks
- **Mood Color Generation**: Unique color generated from audio feature analysis (energy, valence, acousticness)
- **Audio Feature Analysis**: 5-dimension personality profile (energy, danceability, valence, acousticness, instrumentalness)
- **Genre Personality**: Top genre detection with intelligent interpretation
- **Shareable Vibe Receipts**: Beautiful gradient cards exportable as PNG images
- **Social Sharing**: Share your vibe on Twitter, Instagram, or via clipboard link
- **Genre-Aware Descriptions**: Smart interpretation engine that understands 10+ music genres
- **Color Psychology**: HSL-based mood interpretation for accurate emotional mapping

### Statistics & Analytics
- **Listening Statistics**: Track your listening habits and favorite artists
- **Wrapped Feature**: Annual summary of your listening history
- **User Activity Tracking**: Monitor your music discovery journey
- **Detailed Analytics**: View play counts, listening trends, and more
- **Sonic Aura Dashboard**: View your music personality profile and vibe analytics

### Intelligent Music Discovery (Phase 4: "The Frequency")
- **Dual-Axis Discovery**: Select genre + mood color for personalized recommendations
- **3D Orb Visualization**: Interactive Three.js visualization that responds to color selection
- **Color-to-Audio Mapping**: Advanced algorithm mapping RGB values to audio features
  - Brightness → Energy (bright = energetic, dark = laid-back)
  - Saturation → Danceability (saturated = danceable, muted = introspective)
  - Hue → Valence (warm = happy, cool = introspective)
- **50+ Genre Support**: Browse and search through Spotify's complete genre seed list
- **12-Color Mood Palette**: Psychologically-tuned color selection
- **Smart Vibe Descriptions**: AI-like descriptions generated from genre + audio features
- **Discovery Preview**: HTML5 audio preview of discovered tracks
- **Smart Actions**: Play immediately or add to queue
- **Real-time Search**: Filter genres with instant search results

### Advanced Search Capabilities
- **Player Search**: Search and play songs directly from the player
- **Playlist Search**: Search and add songs to playlists in real-time
- **Hybrid Search**: Combines local database with Spotify API results
- **Debounced Input**: Optimized search with 300ms debounce for performance
- **Song Results with Metadata**: Full artist and album information
- **Discovery Randomizer**: Smart randomization from 20 recommendations per query

## Technical Stack

### Backend
- **Framework**: Django 5.0
- **Database**: SQLite (with PostgreSQL support for production)
- **Authentication**: Spotify OAuth 2.0
- **API Integration**: Spotipy (Spotify Web API client)
- **Task Queue**: Celery with Redis for background tasks
- **Image Processing**: PIL/Pillow for color extraction
- **Async Tasks**: Celery Beat for scheduled operations

### Frontend
- **HTML/CSS/JavaScript**: Vanilla implementation with advanced algorithms
- **Styling**: Tailwind CSS with custom dark theme
- **3D Graphics**: Three.js for interactive orb visualization
- **Icons**: Iconify icon library
- **Fonts**: Inter font family
- **Animation**: 50+ GPU-accelerated CSS animations
- **Color Science**: RGB ↔ HSL conversion for color psychology
- **Canvas API**: Color extraction and image processing
- **HTML5 Audio**: Native preview player integration
- **Real-time Updates**: AJAX for dynamic content loading with optimized debouncing

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
- `GET /music/spotify/disconnect/` - Disconnect Spotify account

### Music Management
- `GET /music/songs/` - List songs
- `GET /music/albums/` - List albums
- `GET /music/artists/` - List artists
- `GET /music/playlists/` - User playlists
- `POST /music/api/playlists/add-song/` - Add song to playlist
- `POST /music/api/playlists/remove-song/` - Remove song from playlist

### Search & Discovery
- `GET /music/api/search/?q=query` - Smart search across songs, artists, albums
- `GET /music/api/albums/by-color/?color=%23ff6b9d` - Filter albums by dominant color
- `GET /music/api/color-palette/` - Get all available colors with counts
- `GET /music/api/frequency-randomizer/?genre=pop&color=%23ff6b9d` - Intelligent discovery

### Playback Control
- `POST /music/api/playback/play/` - Play track
- `POST /music/api/playback/pause/` - Pause playback
- `POST /music/api/playback/next/` - Next track
- `POST /music/api/playback/previous/` - Previous track
- `POST /music/api/playback/seek/` - Seek to position
- `POST /music/api/playback/volume/` - Set volume
- `POST /music/api/playback/shuffle/` - Toggle shuffle
- `POST /music/api/playback/repeat/` - Toggle repeat
- `GET /music/api/playback/state/` - Get current playback state
- `GET /music/api/playback/devices/` - Get available devices
- `POST /music/api/playback/transfer/` - Transfer playback to device

### Queue Management
- `POST /music/api/playback/queue/add/` - Add track to queue
- `GET /music/api/playback/queue/get/` - Get current queue
- `POST /music/api/playback/queue/clear/` - Clear queue

### Personalized Insights
- `GET /music/api/sonic-aura/` - Get Sonic Aura vibe score and analytics
- `GET /music/stats/` - Listening statistics dashboard
- `GET /music/wrapped/` - Annual listening wrapped
- `GET /music/sonic-aura/` - Sonic Aura insights page

### Genre Discovery
- `GET /music/api/genre-seeds/` - Get available genres for discovery

## Usage Guide

### Getting Started
1. Navigate to http://localhost:8000
2. Click "Connect with Spotify"
3. Login with your Spotify account
4. Grant permissions
5. Start using SyroApp's full feature set

### Playing Music (The Deck)
1. Go to Player page
2. Search for songs in the search bar
3. Click the play button or song title
4. Select device if prompted
5. Use the vinyl record and controls to manage playback
6. View dynamic background colors matching the track mood

### Discovering by Color (The Crate)
1. Navigate to "The Crate" from the menu
2. View your album library organized by dominant color
3. Click on a color swatch to filter albums
4. Explore the color palette showing all colors in your library
5. Hover over albums to see title and artist
6. Click albums to view details

### Discovering Your Vibe (Sonic Aura)
1. Go to "Sonic Aura" page
2. The app analyzes your last 50 recently played tracks
3. Receive your personalized vibe score (0-100)
4. View your mood color and audio feature profile
5. Read your personalized genre-aware interpretation
6. Download your Sonic Aura as a PNG card
7. Share on Twitter, Instagram, or copy the link

### Intelligent Discovery (The Frequency)
1. Navigate to "The Frequency" page
2. Select a music genre from the dropdown (search to filter)
3. Select a mood color from the 12-color palette
4. Watch the 3D orb update to match your selection
5. Click "Find My Vibe" to discover a track
6. View the track with audio features and vibe description
7. Play immediately or add to queue
8. Click "Find Another" to discover more with same genre/color

### Creating Playlists
1. Navigate to Playlists
2. Click "Create New Playlist"
3. Enter name and description
4. Add songs via search feature
5. Manage songs in playlist

### Viewing Statistics
- **Dashboard**: Overview of listening activity
- **Stats Page**: Detailed statistics and trends
- **Sonic Aura**: Music personality profile and vibe analytics
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
- Discovery history tracking with favorites
- ML-based personal color preference learning
- Mood-based workout playlist generation
- Theme switching (light/dark toggle)
- Lyrics display with sync
- Podcast support
- High-resolution audio support
- Offline playback capability
- Social user profiles and friend network
- Collaborative playlist creation
- Music recommendations from friends
- Advanced analytics with trend analysis

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
- Django 5.0
- Spotify Web API
- Tailwind CSS
- Three.js (3D visualization)
- PIL/Pillow (image processing)
- Celery + Redis (async tasks)
- html2canvas (PNG export)
- Iconify (icons)
- Inter Font

---

**Version**: 2.0 (Complete Portfolio Transformation)
**Last Updated**: November 25, 2024
**Status**: Production Ready

### Version History
- **v1.0** (October 2024): Basic music player with search and playlist management
- **v2.0** (November 2024): Complete transformation with 4 phases
  - Phase 1: Premium "The Deck" player styling
  - Phase 2: "The Crate" color-based discovery
  - Phase 3: "Sonic Aura" shareable vibe receipts
  - Phase 4: "The Frequency" intelligent discovery with color psychology
