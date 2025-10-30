# Universal Player - Quick Reference

## 🎵 Play a Track

### Simplest Form
```html
<button onclick="playTrack('spotify:track:3n3Ppam7vgaVa1iaRUc9Lp')">
  ▶ PLAY
</button>
```

### With Track Info
```html
<button onclick="playTrack('spotify:track:3n3Ppam7vgaVa1iaRUc9Lp', {
  name: 'Blinding Lights',
  artist: 'The Weeknd',
  album: 'After Hours'
})">
  ▶ PLAY
</button>
```

## 📱 Device Selection

**Automatic:**
```javascript
// Shows device modal if no active device
playTrack('spotify:track:123')
```

**Specific Device:**
```javascript
// Skip modal, play directly on device
playTrackOnDevice('spotify:track:123', 'device-id-123')
```

## 🔔 Notifications

```javascript
// Success
showToast('Track is playing!', 'success')

// Error
showToast('Failed to play track', 'error')

// Info
showToast('Device is offline', 'info')
```

## 📋 Templates Cheat Sheet

### Button in Table
```html
<td>
  <button onclick="playTrack('{{ track.uri }}', {
    name: '{{ track.name|escapejs }}',
    artist: '{{ track.artist|escapejs }}'
  })" class="btn-sm">▶</button>
</td>
```

### Button in Card
```html
<div class="card">
  <h3>{{ track.name }}</h3>
  <p>{{ artist.name }}</p>
  <button onclick="playTrack('{{ track.uri }}', {
    name: '{{ track.name|escapejs }}',
    artist: '{{ artist.name|escapejs }}'
  })" class="btn btn-play">▶ PLAY</button>
</div>
```

### Button in List
```html
<li>
  {{ track.name }}
  <button onclick="playTrack('{{ track.uri }}')" class="btn-inline">▶</button>
</li>
```

## 🚀 Endpoints

### Get Devices
```
GET /music/api/playback/devices/

Response:
{
  "status": "success",
  "devices": [
    {
      "id": "device-123",
      "name": "My Computer",
      "type": "Computer",
      "is_active": true
    }
  ],
  "has_active_device": true
}
```

### Play Track
```
POST /music/api/playback/play/

Parameters:
- uri: 'spotify:track:123' (required)
- device_id: 'device-123' (optional)

Response:
{
  "status": "success",
  "message": "Playing track"
}
```

## 🎯 Track URI Formats

| Object | URI Format | Example |
|--------|-----------|---------|
| Track | `spotify:track:ID` | `spotify:track:3n3Ppam7vgaVa1iaRUc9Lp` |
| Album | `spotify:album:ID` | `spotify:album:4aawyAB9zYcIXVofZnoTQN` |
| Playlist | `spotify:playlist:ID` | `spotify:playlist:37i9dQZF1DXcBWIGoYBM5M` |
| Artist | `spotify:artist:ID` | `spotify:artist:1Xyo4u8uhalNMyVIJ1YVA` |

## 🐛 Debugging

### Check Console (F12)
```javascript
// Play with debug info
console.log('Playing:', trackUri);
playTrack(trackUri);
```

### Test Endpoint
```javascript
fetch('/music/api/playback/devices/')
  .then(r => r.json())
  .then(console.log)
```

### Check Token
```javascript
// Token should be available
console.log(document.querySelector('[data-csrf-token]'));
```

## ⚠️ Common Mistakes

| ❌ Wrong | ✅ Correct |
|---------|-----------|
| `'spotify:track:'` | `'spotify:track:3n3Ppam7...'` |
| `name: Track Name` | `name: 'Track Name'` |
| `{{ name }}` | `{{ name\|escapejs }}` |
| `playMusic()` | `playTrack()` |
| No CSRF token | Included in POST |

## 📱 Spotify Device Types

```javascript
{
  "type": "Computer",     // 🖥️ Desktop/Laptop
  "type": "Smartphone",   // 📱 iPhone/Android
  "type": "Speaker",      // 🔊 Smart speakers
  "type": "TV",          // 📺 Smart TVs
  "type": "AVR",         // 🎛️ Audio receivers
  "type": "STR_RECEIVER"  // 🎛️ String receiver
}
```

## 🎨 CSS Classes Available

```css
.device-modal-overlay    /* Modal background */
.device-modal           /* Modal box */
.modal-header           /* Title */
.device-option          /* Device button */
.device-option:hover    /* Device hover */
.toast-notification     /* Toast box */
.toast-notification.success  /* Success toast */
.toast-notification.error    /* Error toast */
```

## 🔑 Key Variables

```javascript
window.syroPlayer = {
  pendingTrackUri: null,     // Track waiting to play
  pendingTrackInfo: null     // Track metadata
}
```

## 🔄 Flow Diagram

```
User clicks play button
        ↓
playTrack(uri, info)
        ↓
Fetch /music/api/playback/devices/
        ↓
    ┌───┴────────────┐
    ↓                ↓
Has active      No active
device?          device?
    ↓                ↓
Play now        Show modal
    ↓                ↓
    │          User selects
    │          device
    │                ↓
    └────────┬───────┘
             ↓
   POST /music/api/playback/play/
             ↓
        Music plays! 🎵
```

## 📚 Full Documentation

- **UNIVERSAL_PLAYER_SETUP.md** - Complete setup
- **ADDING_PLAY_TO_PAGES.md** - Page integration
- **PLAYER_IMPLEMENTATION_GUIDE.md** - API reference
- **IMPLEMENTATION_SUMMARY.md** - Full summary

## ✅ Checklist for Adding Play Buttons

- [ ] Include track URI (spotify:track:ID)
- [ ] Use escapejs filter for text
- [ ] Test on search page first
- [ ] Test with multiple devices
- [ ] Test on mobile
- [ ] Check browser console for errors
- [ ] Verify button renders
- [ ] Verify click triggers play
- [ ] Verify toast notification shows

## 🎬 Examples

### Search Results
```html
<button onclick="playTrack('{{ track.uri }}', {
  name: '{{ track.name|escapejs }}',
  artist: '{% for a in track.artists %}{{ a.name }}{% endfor %}'
})">▶ PLAY</button>
```

### Artist Page
```html
<button onclick="playTrack('spotify:track:{{ song.spotify_id }}', {
  name: '{{ song.title|escapejs }}',
  artist: '{{ artist.name|escapejs }}'
})">▶</button>
```

### Playlist
```html
<button onclick="playTrack('spotify:track:{{ song.id }}', {
  name: '{{ song.title|escapejs }}'
})">▶</button>
```

---

**Status:** ✅ Ready to use
**Last Updated:** 2025-10-29
