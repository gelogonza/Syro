# SyroMusic Advanced Features Guide

## Overview

SyroMusic now includes 9 advanced features that enhance user experience, social connectivity, and music discovery. All features are production-ready with full API support and frontend integration.

---

## 1. Search History

### Description
Automatically tracks and displays user search history for quick access to previous queries.

### Features
- Save searches with query and type (all, artist, album, track, playlist)
- Display last 20 unique searches
- Clear entire search history
- Click to re-search previous queries

### API Endpoints
```
GET  /music/api/search-history/        - Get user's search history
POST /music/api/search-history/        - Save a search
POST /music/api/search-history/clear/  - Clear all history
```

### Frontend Usage
```javascript
// Save a search
await SearchHistory.save('The Weeknd', 'artist');

// Get search history
const history = await SearchHistory.get(20);

// Display in UI
SearchHistory.displayHistory('search-history-container');

// Clear all history
await SearchHistory.clear();
```

### Database
- **Model**: `SearchHistory`
- **Fields**: user, query, search_type, created_at
- **Indexed**: user, created_at

---

## 2. Mini Player Widget

### Description
Floating mini player that stays visible while users browse other pages.

### Features
- Fixed position widget (bottom-right)
- Minimize/expand toggles
- Display current track info with album art
- Quick controls: play/pause, next track, like
- Saves state in localStorage
- Draggable and closeable

### Frontend Usage
```javascript
// Initialize
MiniPlayer.init();

// Update with track data
MiniPlayer.updateTrack(trackData);

// Toggle visibility
MiniPlayer.toggle();
MiniPlayer.hide();
MiniPlayer.show();

// Control playback
MiniPlayer.playPause();
MiniPlayer.nextTrack();
```

### Customization
The widget dimensions and position can be customized in `features.js`:
- Position: `bottom-4 right-4` (Tailwind classes)
- Width: `w-80` (320px)
- Adjust in the `createWidget()` method

---

## 3. Playlist Collaboration

### Description
Allow multiple users to collaborate on playlists with different permission levels.

### Features
- Add collaborators with three permission levels:
  - View Only: Read-only access
  - Can Edit: Add/remove songs
  - Admin: Full control including collaborator management
- Share playlists with personal messages
- Track all collaborators and their permissions

### API Endpoints
```
POST /music/api/collaborator/      - Add/update collaborator
POST /music/api/share-playlist/    - Share playlist with user
```

### Frontend Usage
```javascript
// Add collaborator to playlist
await PlaylistCollaboration.addCollaborator(playlistId, 'username', 'edit');

// Share playlist with message
await PlaylistCollaboration.sharePlaylist(playlistId, 'username', 'Check out my playlist!');
```

### Database
- **Model**: `PlaylistCollaborator`
- **Fields**: playlist, user, permission_level, created_at
- **Constraint**: Unique(playlist, user)

- **Model**: `PlaylistShare`
- **Fields**: playlist, shared_by, shared_with, message, created_at
- **Constraint**: Unique(playlist, shared_by, shared_with)

---

## 4. Social Features

### Description
Enable user profiles, following relationships, and social discovery.

### Features
- Public/private user profiles
- Follow/unfollow other users
- Display follower/following counts
- User bio and profile image
- Favorite genre tracking

### API Endpoints
```
GET  /music/api/profile/          - Get user profile
POST /music/api/profile/          - Update profile
POST /music/api/follow/           - Follow user
POST /music/api/unfollow/         - Unfollow user
```

### Frontend Usage
```javascript
// Get user profile
const profile = await SocialFeatures.userProfile.get();

// Update profile
await SocialFeatures.userProfile.update({
  bio: 'Music enthusiast',
  profile_image: 'https://...',
  favorite_genre: 'Pop',
  is_public: true
});

// Follow user
await SocialFeatures.followUser('username');

// Unfollow user
await SocialFeatures.unfollowUser('username');
```

### Database
- **Model**: `UserProfile` (Enhanced)
- **New Fields**: bio (500 chars), profile_image (URL), is_public (boolean)

- **Model**: `UserFollowing`
- **Fields**: follower, following, created_at
- **Constraint**: Unique(follower, following)
- **Indexes**: (follower, -created_at), (following, -created_at)

---

## 5. Offline Mode

### Description
Enable the app to work offline using Service Workers and caching strategies.

### Features
- Automatic Service Worker registration
- Cache important pages and assets
- Online/offline status detection
- Auto-sync when connection restored
- LocalStorage for offline data
- Network-first strategy for API calls

### How It Works
1. Service Worker installed and activated on first page load
2. Static assets cached on demand (network-first)
3. User can continue browsing cached pages offline
4. API calls fail gracefully with cached data fallback
5. Auto-sync triggers when app comes back online

### Frontend Usage
```javascript
// Initialize (automatic on DOMContentLoaded)
OfflineMode.init();

// Check online status
if (OfflineMode.isOnline) {
  // Fetch fresh data
} else {
  // Use cached data
}

// Cache data
OfflineMode.cacheData('tracks', trackList);

// Retrieve cached data
const cachedTracks = OfflineMode.getCachedData('tracks');

// Manual sync
OfflineMode.syncData();
```

### Configuration
Service Worker cache settings in `sw.js`:
```javascript
const CACHE_NAME = 'syromusic-v1';
const urlsToCache = [
  '/',
  '/music/player/',
  '/music/dashboard/',
  // Add more URLs to cache
];
```

---

## 6. Track Lyrics Display

### Description
Display synchronized lyrics for the currently playing track.

### Features
- Fetch lyrics from Genius or other sources
- Modal popup display
- Cached lyrics for performance
- Explicit content flagging
- Source attribution

### API Endpoints
```
GET /music/api/lyrics/?spotify_track_id=xxx  - Get track lyrics
```

### Frontend Usage
```javascript
// Get lyrics for a track
const lyrics = await TrackLyrics.get('spotify_track_id');

// Display in modal
TrackLyrics.showModal('Track Name', 'spotify_track_id');

// Manual display in container
TrackLyrics.display(lyricsData, 'lyrics-container');
```

### Database
- **Model**: `TrackLyrics`
- **Fields**: spotify_track_id (unique), track_name, artist_name, lyrics (text), lyrics_source, is_explicit, created_at, updated_at
- **Index**: spotify_track_id

### Adding Lyrics
To populate the lyrics database, you'll need to integrate with a lyrics API:

```python
# Example: Integrate with Genius API
import requests

def fetch_and_cache_lyrics(track_name, artist_name, spotify_track_id):
    # Fetch from Genius API
    response = requests.get('https://api.genius.com/search', params={
        'q': f'{track_name} {artist_name}',
        'access_token': GENIUS_API_TOKEN
    })

    result = response.json()['response']['hits'][0]['result']

    # Cache in database
    TrackLyrics.objects.update_or_create(
        spotify_track_id=spotify_track_id,
        defaults={
            'track_name': track_name,
            'artist_name': artist_name,
            'lyrics': fetch_lyrics_from_url(result['url']),
            'lyrics_source': 'genius'
        }
    )
```

---

## 7. Audio Visualization

### Description
Dynamic audio visualizations that react to music playback.

### Features
- 4 visualization styles:
  1. **Bars**: Frequency bars with color gradient
  2. **Waveform**: Smooth line following audio
  3. **Circles**: Pulsing circles based on volume
  4. **Spectrum**: Color spectrum animation
- Style persistence in localStorage
- Real-time frequency analysis
- Customizable colors and animation

### Frontend Usage
```javascript
// Initialize visualizer
AudioVisualizer.init('canvas-id', audioContext, analyser);

// Change style
AudioVisualizer.setStyle('waveform'); // 'bars', 'waveform', 'circles', 'spectrum'

// Load saved style preference
AudioVisualizer.loadSavedStyle();
```

### Integration
To use with player, connect to Web Audio API:

```javascript
const audioContext = new (window.AudioContext || window.webkitAudioContext)();
const analyser = audioContext.createAnalyser();

// Connect audio source
source.connect(analyser);

// Initialize visualizer
AudioVisualizer.init('visualizer-canvas', audioContext, analyser);
```

### Customization
Modify colors in `features.js` drawStyle methods:
```javascript
// Example: Change bar colors
this.ctx.fillStyle = `hsl(${hue}, 100%, 50%)`;
// Adjust hue range or use custom colors
```

---

## 8. Playback History Analytics

### Description
Comprehensive analytics about user's listening habits and patterns.

### Features
- Listening streak counter (consecutive days)
- Most active hour of day (0-23)
- Most active day of week (0-6)
- Total listening minutes
- Unique artists heard
- Unique tracks heard
- Monthly summary data (JSON)
- Analytics dashboard display

### API Endpoints
```
GET /music/api/analytics/  - Get user's playback analytics
```

### Frontend Usage
```javascript
// Get analytics data
const analytics = await PlaybackAnalytics.get();

// Display dashboard
await PlaybackAnalytics.displayDashboard('analytics-container');
```

### Analytics Dashboard
The dashboard displays:
- Listening Streak (days)
- Total Listening Time (hours)
- Unique Artists Count
- Unique Tracks Count
- Most Active Hour and Day

### Database
- **Model**: `PlaybackHistoryAnalytics`
- **Fields**: user (OneToOne), listening_streak, last_listened_date, most_active_hour, most_active_day_of_week, total_listening_minutes, unique_artists_heard, unique_tracks_heard, monthly_summary (JSON)

### Updating Analytics
Create a Celery task to periodically update analytics:

```python
from celery import shared_task

@shared_task
def update_playback_analytics(user_id):
    user = User.objects.get(id=user_id)
    analytics, _ = PlaybackHistoryAnalytics.objects.get_or_create(user=user)

    # Update statistics
    analytics.unique_artists_heard = UserListeningActivity.objects\
        .filter(user=user)\
        .values('artist_name')\
        .distinct()\
        .count()

    analytics.total_listening_minutes = sum([
        activity.duration_ms // 60000
        for activity in UserListeningActivity.objects.filter(user=user)
    ])

    analytics.save()
```

---

## 9. Smart Queue Management

### Description
Advanced queue management with drag-and-drop reordering and visual feedback.

### Features
- View full queue with track details
- Drag-and-drop reordering
- Visual position indicators
- Real-time database updates
- Album art display
- Artist information

### API Endpoints
```
GET  /music/api/queue/reorder/         - Get current queue items
POST /music/api/queue/reorder/update/  - Update queue positions
```

### Frontend Usage
```javascript
// Get queue items
const items = await SmartQueue.get();

// Render queue with drag-and-drop
await SmartQueue.renderQueue('queue-container');

// Update positions (automatic on drag)
await SmartQueue.updatePositions([item1_id, item2_id, item3_id]);
```

### Database
- **Model**: `QueueItem`
- **Fields**: queue (FK), track_data (JSON), position (integer), created_at, updated_at
- **Constraints**: Unique(queue, track_data)
- **Indexes**: (queue, position)

### Track Data Format
```json
{
  "id": "spotify_track_id",
  "name": "Track Name",
  "artists": [{"name": "Artist Name"}],
  "album": {
    "name": "Album Name",
    "images": [{"url": "image_url"}]
  },
  "duration_ms": 180000
}
```

---

## Integration Guide

### 1. Add to Player Page
```html
<!-- Include script in base template or player template -->
<script src="{% static 'js/features.js' %}"></script>

<!-- Initialize features -->
<script>
  document.addEventListener('DOMContentLoaded', function() {
    MiniPlayer.init();
    OfflineMode.init();
    AudioVisualizer.loadSavedStyle();
  });
</script>
```

### 2. Add UI Elements
```html
<!-- Search history -->
<div id="search-history"></div>

<!-- Lyrics button in player -->
<button id="lyrics-button">Show Lyrics</button>

<!-- Visualizer style selector -->
<select id="visualizer-style">
  <option value="bars">Bars</option>
  <option value="waveform">Waveform</option>
  <option value="circles">Circles</option>
  <option value="spectrum">Spectrum</option>
</select>

<!-- Analytics dashboard -->
<div id="analytics-dashboard"></div>

<!-- Queue container -->
<div id="queue-container"></div>
```

### 3. Add API Imports
All models are already imported in `api_views.py`. No additional configuration needed.

### 4. URL Configuration
All routes are already configured in `urls.py`. No additional setup required.

---

## Security Considerations

All features include:
- CSRF token validation on POST requests
- User authentication requirements
- Permission level checking for collaboration
- Input validation and sanitization
- Error handling with graceful degradation
- Rate limiting ready (can add in settings)

---

## Performance Optimization

### Caching
- Search history cached in localStorage (client-side)
- Lyrics cached in database
- Analytics data stored in database
- Service Worker caches static assets

### Database Indexes
All models include proper indexes for:
- User-specific queries
- Created date sorting
- Foreign key lookups
- Composite indexes for common filters

### Frontend Optimization
- Debounced search history saves
- Lazy loading for lyrics modal
- Efficient DOM updates
- Service Worker for offline support

---

## Troubleshooting

### Search History Not Saving
- Verify CSRF token is present in forms
- Check browser console for JavaScript errors
- Ensure SearchHistory model migration ran

### Mini Player Not Appearing
- Check JavaScript console for errors
- Verify features.js is loaded
- Ensure MiniPlayer.init() is called

### Offline Mode Not Working
- Check if Service Worker registered (Chrome DevTools -> Application -> Service Workers)
- Verify Service Worker cache is created
- Check browser console for SW errors

### Lyrics Not Displaying
- Verify TrackLyrics model exists in database
- Check if Spotify track ID is correct
- Add lyrics data to database using Genius API

### Analytics Dashboard Empty
- Verify PlaybackHistoryAnalytics model created
- Check if user has listening activity
- Run migration: `python manage.py migrate`

---

## Future Enhancements

Potential features to add:
1. AI-powered recommendations based on listening patterns
2. Podcast integration
3. Playlist collaboration real-time sync
4. Social feed showing friends' activity
5. Music game (genre guessing, etc.)
6. Integration with other music services
7. Advanced filters (BPM, key, energy level)
8. Collaborative playlists with voting

---

## API Reference Summary

### Search History
- `POST /music/api/search-history/` - Save search
- `GET /music/api/search-history/?limit=20` - Get history
- `POST /music/api/search-history/clear/` - Clear all

### Social Features
- `GET /music/api/profile/` - Get profile
- `POST /music/api/profile/` - Update profile
- `POST /music/api/follow/` - Follow user
- `POST /music/api/unfollow/` - Unfollow user

### Collaboration
- `POST /music/api/collaborator/` - Add collaborator
- `POST /music/api/share-playlist/` - Share playlist

### Queue Management
- `GET /music/api/queue/reorder/` - Get queue
- `POST /music/api/queue/reorder/update/` - Update queue order

### Analytics & Lyrics
- `GET /music/api/analytics/` - Get analytics
- `GET /music/api/lyrics/?spotify_track_id=xxx` - Get lyrics

---

## Support & Documentation

For more information or issues:
1. Check browser console for errors
2. Review Django logs: `python manage.py runserver` output
3. Check database migrations: `python manage.py showmigrations`
4. Verify API endpoints: `python manage.py urls`

---

**Last Updated**: October 30, 2025
**SyroMusic Version**: 2.0+
