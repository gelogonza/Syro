# Adding Play Buttons to Other Pages

Now that you have the universal player system, adding play buttons to other pages is simple!

## Quick Template Snippets

### 1. Playlists Detail Page
**File:** `SyroMusic/templates/syromusic/playlist_detail.html`

Find your song list and add a play button:

```html
{% for song in playlist.song_set.all %}
  <tr>
    <td>{{ song.title }}</td>
    <td>{{ song.album.artist.name }}</td>
    <td>
      <button onclick="playTrack('spotify:track:{{ song.spotify_id }}', {
        name: '{{ song.title|escapejs }}',
        artist: '{{ song.album.artist.name|escapejs }}',
        album: '{{ song.album.title|escapejs }}'
      })"
        class="btn btn-play">
        ▶ PLAY
      </button>
    </td>
  </tr>
{% endfor %}
```

### 2. Artist Detail Page
**File:** `SyroMusic/templates/syromusic/artist_detail.html`

Add play button to artist's top tracks:

```html
<!-- Album Section -->
{% for album in artist.albums.all %}
  <div class="album-card">
    <h3>{{ album.title }}</h3>

    <!-- Songs in Album -->
    {% for song in album.song_set.all %}
      <div class="song-item">
        <span>{{ song.title }}</span>
        <button onclick="playTrack('spotify:track:{{ song.spotify_id }}', {
          name: '{{ song.title|escapejs }}',
          artist: '{{ artist.name|escapejs }}',
          album: '{{ album.title|escapejs }}'
        })"
          class="btn-sm btn-play">
          ▶
        </button>
      </div>
    {% endfor %}
  </div>
{% endfor %}
```

### 3. Album Detail Page
**File:** `SyroMusic/templates/syromusic/album_detail.html`

Add play button to all album tracks:

```html
<div class="track-list">
  {% for song in album.song_set.all %}
    <div class="track-row">
      <span class="track-number">{{ song.track_number }}</span>
      <span class="track-name">{{ song.title }}</span>
      <span class="track-duration">{{ song.duration }}</span>
      <button onclick="playTrack('spotify:track:{{ song.spotify_id }}', {
        name: '{{ song.title|escapejs }}',
        artist: '{{ album.artist.name|escapejs }}',
        album: '{{ album.title|escapejs }}'
      })"
        class="btn-play">
        ▶ PLAY
      </button>
    </div>
  {% endfor %}
</div>
```

### 4. Recommendations Page
**File:** `SyroMusic/templates/syromusic/recommendations.html`

Add play button to recommended tracks:

```html
<div class="recommendations-grid">
  {% for track in recommendations %}
    <div class="track-card">
      <img src="{{ track.image }}" alt="{{ track.name }}">
      <h3>{{ track.name }}</h3>
      <p>{{ track.artist }}</p>
      <button onclick="playTrack('{{ track.uri }}', {
        name: '{{ track.name|escapejs }}',
        artist: '{{ track.artist|escapejs }}',
        album: '{{ track.album|escapejs }}'
      })"
        class="btn btn-primary">
        ▶ PLAY
      </button>
    </div>
  {% endfor %}
</div>
```

### 5. Browse/Genres Page
**File:** `SyroMusic/templates/syromusic/browse_genres.html`

Add play button to genre tracks:

```html
{% for genre in genres %}
  <div class="genre-section">
    <h3>{{ genre.name }}</h3>
    <div class="track-list">
      {% for track in genre.tracks %}
        <div class="track-item">
          <span>{{ track.name }}</span>
          <span>{{ track.artist }}</span>
          <button onclick="playTrack('{{ track.uri }}', {
            name: '{{ track.name|escapejs }}',
            artist: '{{ track.artist|escapejs }}'
          })"
            class="btn-play">
            ▶
          </button>
        </div>
      {% endfor %}
    </div>
  </div>
{% endfor %}
```

## Common Button Styles

### Inline Button (Small)
```html
<button onclick="playTrack('{{ track.uri }}')"
        class="btn btn-sm">
  ▶
</button>
```

### Full Button (Medium)
```html
<button onclick="playTrack('{{ track.uri }}', {
  name: '{{ track.name|escapejs }}'
})"
        class="btn btn-md">
  ▶ PLAY
</button>
```

### Featured Button (Large)
```html
<button onclick="playTrack('{{ track.uri }}', {
  name: '{{ track.name|escapejs }}',
  artist: '{{ artist.name|escapejs }}',
  album: '{{ album.name|escapejs }}'
})"
        class="btn btn-lg btn-primary">
  ▶ PLAY NOW
</button>
```

## Important Notes

### Track URI Format
✅ **Correct:** `'spotify:track:3n3Ppam7vgaVa1iaRUc9Lp'`
❌ **Wrong:** `'spotify:track:'` (incomplete ID)
❌ **Wrong:** `'track:3n3Ppam7vgaVa1iaRUc9Lp'` (missing 'spotify:')

### Escaping Track Information
Always use `|escapejs` filter for user-provided content:

```html
<!-- ✅ CORRECT -->
name: '{{ track.name|escapejs }}'

<!-- ❌ WRONG - Can break JavaScript if name has quotes -->
name: '{{ track.name }}'
```

### Optional Track Info
You can pass minimal or full track info:

```javascript
// Minimal - just URI
playTrack('spotify:track:123');

// With name
playTrack('spotify:track:123', { name: 'Track Name' });

// Full info (best UX)
playTrack('spotify:track:123', {
  name: 'Track Name',
  artist: 'Artist Name',
  album: 'Album Name'
});
```

## CSS Styling Examples

### Simple Button
```css
.btn-play {
  background: none;
  border: 1px solid #ccc;
  padding: 0.5rem;
  cursor: pointer;
  border-radius: 4px;
}

.btn-play:hover {
  background: #f0f0f0;
}
```

### Modern Button
```css
.btn-play {
  background: linear-gradient(135deg, #10b981, #22c55e);
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s ease;
}

.btn-play:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}
```

### Spotify Green
```css
.btn-play {
  background: #1DB954;
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 24px;
  cursor: pointer;
  font-weight: bold;
}

.btn-play:hover {
  background: #1ed760;
}
```

## Testing Checklist

For each page you add play buttons to:

- [ ] Button renders correctly
- [ ] Button text visible
- [ ] Click play button
- [ ] Device modal appears (if no active device)
- [ ] Select device from list
- [ ] Music starts playing on device
- [ ] Toast notification shows
- [ ] Test with different devices
- [ ] Test on mobile
- [ ] Test with no devices available

## Common Issues & Solutions

### Issue: Button Doesn't Work
**Check:**
- Is player modal included in `base.html`? ✅
- Is track URI in correct format? ✅
- Is browser console clear of errors? ✅

### Issue: Modal Doesn't Show
**Check:**
- Are you using correct function name `playTrack()`? ✅
- Is CSRF token available? ✅
- Check browser developer tools (F12)

### Issue: Track Info Not Showing
**Check:**
- Used `|escapejs` filter? ✅
- Proper format: `name: 'track name'` ✅
- No quotes in track info causing JS errors? ✅

## Track URI Reference

Different Spotify object types have different URIs:

```javascript
// Track
playTrack('spotify:track:3n3Ppam7vgaVa1iaRUc9Lp', {...})

// Album (plays first track)
playTrack('spotify:album:4aawyAB9zYcIXVofZnoTQN', {...})

// Playlist (plays first track)
playTrack('spotify:playlist:37i9dQZF1DXcBWIGoYBM5M', {...})

// Artist (plays related tracks)
playTrack('spotify:artist:1Xyo4u8uhalNMiyVIJ1YVA', {...})
```

## Best Practices

✅ **Do:**
- Always include track info for better UX
- Use `|escapejs` filter for safe escaping
- Test play button on different devices
- Show confirmation/error toasts
- Keep button design consistent

❌ **Don't:**
- Forget CSRF token
- Use incomplete track URIs
- Mix escaped and unescaped data
- Call API directly - use `playTrack()` function
- Leave broken buttons in code

## Future Enhancements

After implementing play buttons everywhere:

1. **Add to Queue** - Add tracks to current playback queue
2. **Save to Playlist** - Save tracks directly from any page
3. **Add to Favorites** - Mark tracks as liked
4. **Share Track** - Generate shareable link
5. **View Lyrics** - Show track lyrics while playing
6. **Similar Tracks** - Show recommendations based on track

---

Need help? Check the full guide: [UNIVERSAL_PLAYER_SETUP.md](UNIVERSAL_PLAYER_SETUP.md)
