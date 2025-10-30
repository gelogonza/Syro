# Universal Player Setup - Quick Start

## What Was Done

You now have a unified music playback system that works from **any page** in your app. No more "No active device found" errors!

## Changes Made

### 1. **Backend Endpoints**
- ✅ Added `/music/api/playback/devices/` endpoint to get available devices
- ✅ Enhanced `play_track` endpoint to handle device selection

**Location:** [playback_views.py:392-440](SyroMusic/playback_views.py#L392-L440)

### 2. **URL Configuration**
- ✅ Added `get_devices` route to `/music/api/playback/devices/`

**Location:** [urls.py:31](SyroMusic/urls.py#L31)

### 3. **Universal Player Modal**
- ✅ Created reusable device selector modal component
- ✅ Shows automatic device selection when needed
- ✅ Toast notifications for user feedback

**Location:** [player_modal.html](SyroMusic/templates/syromusic/player_modal.html)

### 4. **Base Template Integration**
- ✅ Included player modal in base template

**Location:** [base.html:431](SyroMusic/templates/base.html#L431)

### 5. **Search Results Enhancement**
- ✅ Updated track play buttons to use universal player
- ✅ Updated Spotify track buttons with full track info
- ✅ Updated album play with track info

**Location:** [search.html](SyroMusic/templates/syromusic/search.html)

## How to Use

### In Any Template

Add play button for any track:

```html
<button onclick="playTrack('spotify:track:TRACK_ID', {
  name: 'Track Name',
  artist: 'Artist Name',
  album: 'Album Name'
})" class="btn btn-play">
  ▶ PLAY
</button>
```

### The Flow

1. **User clicks play** → Calls `playTrack(trackUri, trackInfo)`
2. **System checks devices** → Fetches from `/music/api/playback/devices/`
3. **If active device exists** → Play immediately ✅
4. **If no active device** → Show device selector modal 📱
5. **User selects device** → Start playback on that device 🎵

## Files Modified

- `SyroMusic/playback_views.py` - Added `get_available_devices()` endpoint
- `SyroMusic/urls.py` - Added `/api/playback/devices/` route
- `SyroMusic/templates/base.html` - Included player modal
- `SyroMusic/templates/syromusic/search.html` - Enhanced play buttons

## Files Created

- `SyroMusic/templates/syromusic/player_modal.html` - Universal player component
- `PLAYER_IMPLEMENTATION_GUIDE.md` - Detailed implementation guide

## JavaScript API

### `playTrack(trackUri, trackInfo)`
Play a track with automatic device selection.

**Example:**
```javascript
playTrack('spotify:track:3n3Ppam7vgaVa1iaRUc9Lp', {
  name: 'Blinding Lights',
  artist: 'The Weeknd',
  album: 'After Hours'
});
```

### `showToast(message, type)`
Show notification toast.

**Example:**
```javascript
showToast('Track is now playing!', 'success');
showToast('Failed to play track', 'error');
```

## Error Handling

### No Devices Available
**Error:** "No Spotify devices available"
**Fix:** Open Spotify on any device (computer, phone, speaker)

### No Active Device
**Solution:** Modal automatically shows all devices for selection

### Device Offline
**Solution:** Modal shows only online/available devices

## Testing

### Test Flow
1. Open Spotify on a device (computer, phone, or speaker)
2. Go to search page
3. Search for a song
4. Click "▶ Play" button
5. If you have active device → Plays immediately ✅
6. If no active device → Shows device selector modal
7. Select a device → Music plays on that device 🎵

### Test Pages
- ✅ Search Results - Spotify tracks and albums
- ✅ Local Song Results - Database songs
- ✅ Coming Soon: Playlists, Artist pages, Album pages

## Next Steps

### To Add Play to More Pages

1. **Playlists Page** - Add button to playlist_detail.html
2. **Artist Pages** - Add button to artist_detail.html
3. **Album Pages** - Add button to album_detail.html
4. **Recommendations** - Add button to recommendations.html
5. **Browse/Genres** - Add button to browse_genres.html

### Example for Playlists

In `playlist_detail.html`, find the song list and add:

```html
<button onclick="playTrack('spotify:track:{{ song.spotify_id }}', {
  name: '{{ song.title|escapejs }}',
  artist: '{{ song.artist|escapejs }}'
})" class="btn btn-play">
  ▶ PLAY
</button>
```

## Troubleshooting

### Player Modal Doesn't Appear
- ✅ Check that `base.html` includes `player_modal.html`
- ✅ Clear browser cache and reload

### Device Selector Always Shows
- ✅ Open Spotify on a device to make it active
- ✅ Restart Spotify if device appears offline

### Play Button Not Working
- ✅ Check browser console for errors (F12)
- ✅ Verify Spotify URI format: `spotify:track:XXXX`
- ✅ Check that CSRF token is available

### No Toast Notification Shows
- ✅ Modal was closed automatically after play
- ✅ Toast disappears after 4 seconds

## Security Notes

✅ **CSRF Protection** - All POST requests use CSRF token
✅ **Token Refresh** - Automatic token refresh before API calls
✅ **User Isolation** - Only own devices accessible
✅ **Error Handling** - Graceful error messages

## Performance

- Device list fetched on-demand (not cached)
- Modal closes automatically after selection
- Toast notifications auto-dismiss
- Minimal JavaScript bundle size
- No external dependencies required

## Browser Compatibility

✅ Chrome/Edge 90+
✅ Firefox 88+
✅ Safari 14+
✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Spotify API Notes

- Requires Spotify OAuth with these scopes:
  - `user-read-playback-state` ✅ (newly added)
  - `user-modify-playback-state` ✅ (newly added)
  - `streaming` ✅

- Device must have active Spotify app open
- Private session on device will show in device list but playback may fail
- Premium account required for playback control on non-owned devices

## Next Enhancement Ideas

1. **Remember Last Device** - Store device preference per user
2. **Device Status Indicator** - Show online/offline status
3. **Auto-Play Next** - Continue playing similar music
4. **Queue Display** - Show upcoming tracks from device
5. **Volume Control** - Adjust volume per device
6. **Playback Sync** - Show what friends are playing

---

**Ready to use!** Test by searching for a song and clicking the play button.
