# Universal Player Implementation Guide

## Overview

You now have a unified playback system that allows playing tracks from **any page** (search, playlists, player, etc.) with automatic device selection.

## How It Works

1. **User clicks play** on a track from anywhere in your app
2. **System fetches available Spotify devices**
3. **If active device exists** → Play immediately
4. **If no active device** → Show device selector modal
5. **User selects device** → Play starts on that device

## Integration Guide

### Step 1: Include Player Modal in Base Template

Add this to your `base.html` right before the closing `</body>` tag:

```html
{% include 'SyroMusic/player_modal.html' %}
```

### Step 2: Add Play Button to Search Results

In your `search.html` template, add a play button to each track:

```html
{% for track in spotify_results %}
  <div class="track-item">
    <h3>{{ track.name }}</h3>
    <p>{{ track.artist }}</p>

    <!-- Add this button -->
    <button onclick="playTrack('{{ track.uri }}', {
      name: '{{ track.name|escapejs }}',
      artist: '{{ track.artist|escapejs }}',
      album: '{{ track.album|escapejs }}'
    })" class="play-btn">
      ▶ PLAY
    </button>
  </div>
{% endfor %}
```

### Step 3: Add Play Button to Playlists

In your `playlist_detail.html`, add play buttons to songs:

```html
{% for song in playlist.song_set.all %}
  <tr>
    <td>{{ song.title }}</td>
    <td>
      <button onclick="playTrack('spotify:track:{{ song.spotify_id }}', {
        name: '{{ song.title|escapejs }}',
        artist: '{{ song.artist|escapejs }}'
      })" class="small-btn">
        ▶
      </button>
    </td>
  </tr>
{% endfor %}
```

### Step 4: Enhance Artist/Album Pages

Add play buttons to browse your music library:

```html
<!-- In artist_detail.html or album_detail.html -->
<button onclick="playTrack('{{ track.spotify_uri }}', {
  name: '{{ track.name|escapejs }}',
  artist: '{{ artist.name|escapejs }}'
})" class="play-btn">
  ▶ PLAY TRACK
</button>
```

## JavaScript API

### playTrack(trackUri, trackInfo)

Play a track with automatic device selection.

**Parameters:**
- `trackUri` (string): Spotify track URI (e.g., `'spotify:track:123abc'`)
- `trackInfo` (object): Optional track metadata
  - `name` (string): Track name
  - `artist` (string): Artist name
  - `album` (string): Album name

**Example:**
```javascript
playTrack('spotify:track:3n3Ppam7vgaVa1iaRUc9Lp', {
  name: 'Blinding Lights',
  artist: 'The Weeknd',
  album: 'After Hours'
});
```

### playTrackOnDevice(trackUri, deviceId, trackInfo)

Play track on a specific device (without modal).

**Parameters:**
- `trackUri` (string): Spotify track URI
- `deviceId` (string): Device ID
- `trackInfo` (object): Track metadata

**Example:**
```javascript
playTrackOnDevice('spotify:track:3n3Ppam7vgaVa1iaRUc9Lp', 'device-id-123', {
  name: 'Blinding Lights',
  artist: 'The Weeknd'
});
```

### showToast(message, type)

Show a notification toast.

**Parameters:**
- `message` (string): Toast message
- `type` (string): `'success'`, `'error'`, or `'info'` (default)

**Example:**
```javascript
showToast('Track added to playlist!', 'success');
showToast('Failed to add track', 'error');
```

## Backend Endpoints

### GET `/music/api/playback/devices/`

Get available devices. Returns:

```json
{
  "status": "success",
  "devices": [
    {
      "id": "device-id-1",
      "name": "My Computer",
      "type": "Computer",
      "is_active": true,
      "volume_percent": 80
    }
  ],
  "active_device": { ... },
  "has_active_device": true
}
```

### POST `/music/api/playback/play/`

Play a track on a device.

**Parameters:**
- `uri` (string): Track URI
- `device_id` (string): Device ID (optional if active device exists)

**Response:**
```json
{
  "status": "success",
  "message": "Playing track"
}
```

## Example Implementations

### Simple Play Button (Search Results)

```html
<button onclick="playTrack('{{ track.uri }}', {
  name: '{{ track.name|escapejs }}'
})" style="padding: 0.5rem 1rem; border: 2px solid #000;">
  ▶ PLAY
</button>
```

### Card-Based Play Button

```html
<div class="track-card">
  <img src="{{ track.image }}" alt="{{ track.name }}">
  <h3>{{ track.name }}</h3>
  <p>{{ track.artist }}</p>
  <button onclick="playTrack('{{ track.uri }}', {
    name: '{{ track.name|escapejs }}',
    artist: '{{ track.artist|escapejs }}',
    album: '{{ track.album|escapejs }}'
  })" class="btn-primary">
    ▶ PLAY NOW
  </button>
</div>
```

### Table Row Play Button

```html
<tbody>
  {% for track in tracks %}
    <tr>
      <td>{{ track.title }}</td>
      <td>{{ track.artist }}</td>
      <td>{{ track.duration }}</td>
      <td>
        <button onclick="playTrack('{{ track.spotify_uri }}', {
          name: '{{ track.title|escapejs }}',
          artist: '{{ track.artist|escapejs }}'
        })" class="btn-sm btn-play">
          ▶
        </button>
      </td>
    </tr>
  {% endfor %}
</tbody>
```

## Troubleshooting

### "No Spotify devices available" Error

**Cause:** No Spotify app is open/active on any device

**Solution:**
- Open Spotify on your computer, phone, or speaker
- Wait a few seconds for it to register with Spotify API
- Try playing again

### "No active device found" But I Have Devices

**Cause:** Selected device is offline or not responding

**Solution:**
- Make sure the device has Spotify open
- Restart Spotify on the device
- Select a different device

### Play Button Not Appearing

**Cause:** Player modal not included in base template

**Solution:**
- Add `{% include 'SyroMusic/player_modal.html' %}` to `base.html`
- Clear browser cache

### Device Modal Doesn't Show

**Cause:** Devices endpoint returning error

**Solution:**
- Check that you added `/api/playback/devices/` to `urls.py`
- Check Django console for errors
- Verify Spotify token is still valid

## CSS Styling

The player modal uses brutalist design. To customize:

1. **Modal Width:**
   ```css
   .device-modal {
     max-width: 500px; /* Change from 400px */
   }
   ```

2. **Button Colors:**
   ```css
   .device-option:hover {
     background: #1DB954; /* Spotify green */
     color: white;
   }
   ```

3. **Toast Position:**
   ```css
   .toast-notification {
     bottom: 50px; /* Change from 20px */
     right: 50px;
   }
   ```

## Best Practices

✅ **Do:**
- Include track info for better user experience
- Handle errors gracefully
- Show toasts for feedback
- Test with different devices

❌ **Don't:**
- Forget to include player modal in base template
- Use invalid Spotify URIs
- Call play without token refresh
- Leave device modal open on page navigation

## Future Enhancements

- Auto-select previously used device
- Remember device preference
- Queue next track automatically
- Add playlist play functionality
- Show current playing track across pages
