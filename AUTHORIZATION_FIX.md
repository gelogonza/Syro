# Fix: "No Active Device" - Re-Authorization Required

## The Problem

You're getting "No active device found" errors because the new scopes were added:
- `user-read-playback-state` ✅ (required to read playback info)
- `user-modify-playback-state` ✅ (required to control playback)

Your current Spotify authorization **does NOT include these scopes**, so the API blocks the requests.

## The Solution

### Option 1: Full Re-Authorization (Recommended)

**Step 1: Disconnect Spotify**
1. Go to `/music/dashboard/`
2. Click "Disconnect Spotify" button
3. Confirm disconnection

**Step 2: Clear Browser Cache**
- Press `Ctrl+Shift+Delete` (Windows) or `Cmd+Shift+Delete` (Mac)
- Clear cookies and cache
- Close all browser tabs with your app

**Step 3: Re-Connect Spotify**
1. Go to `/music/` or home page
2. Click "Connect with Spotify"
3. Click "Agree" when Spotify asks for permissions
4. You'll see the NEW permissions list including playback scopes ✅

**Step 4: Test Playback**
1. Open Spotify on a device
2. Go to search page
3. Search for a song
4. Click "▶ PLAY"
5. Music should play! 🎵

### Option 2: Force Re-Authorization (Advanced)

If Option 1 doesn't work:

**Step 1: Clear Django Session**
```python
# In Django shell
python manage.py shell

from django.contrib.auth.models import User
from SyroMusic.models import SpotifyUser

# Find your user
user = User.objects.get(username='your_username')

# Delete the Spotify connection
SpotifyUser.objects.filter(user=user).delete()

# Exit shell
exit()
```

**Step 2: Follow Option 1 Steps 2-4 above**

### Option 3: Database Cleanup (If Stuck)

```bash
# This clears all Spotify user data and forces re-auth for all users
python manage.py dbshell

# In SQLite prompt
DELETE FROM SyroMusic_spotifyuser;

# Exit
.exit
```

Then users must re-connect.

---

## Why This Is Happening

### Before (Old Scopes)
```
user-read-private ✅
user-read-email ✅
user-library-read ✅
...
streaming ✅ (only allows PLAYING music, not reading status)
```

### After (New Scopes)
```
user-read-private ✅
user-read-email ✅
user-read-playback-state ✅ NEW! (read current playing info)
user-modify-playback-state ✅ NEW! (control playback)
user-library-read ✅
...
streaming ✅
```

The API now **requires** the new scopes to work with devices.

---

## What Spotify Scopes Do

| Scope | What It Allows |
|-------|---|
| `streaming` | Play music on devices |
| `user-read-playback-state` | Read what's playing (NEW) |
| `user-modify-playback-state` | Pause/resume/skip (NEW) |
| `user-library-read` | Read your saved tracks |
| `playlist-read-private` | Read your playlists |

---

## How to Tell It's Fixed

✅ **Working Signs:**
- Can click play button without "No active device" error
- Device selector modal appears (if no active device)
- Can select device and music plays
- See "Now playing: ..." toast notification

❌ **Still Not Working:**
- Still getting 404 errors
- Device modal doesn't appear
- "Permissions missing" error

---

## Testing After Re-Auth

### Test 1: Basic Playback
1. Open Spotify on your computer
2. In the app, search for "blinding lights"
3. Click "▶ PLAY" on the Spotify result
4. Music should play on your computer

### Test 2: No Active Device
1. Close Spotify on all devices
2. Search for a song
3. Click "▶ PLAY"
4. Modal should show "No active device"
5. Open Spotify on phone
6. Modal should refresh and show your phone
7. Select phone → music plays on phone

### Test 3: Multiple Devices
1. Open Spotify on computer, phone, and speaker (if available)
2. Click play
3. Modal shows all 3 devices
4. Select each one → music plays on that device

---

## Troubleshooting

### "Still getting NO_ACTIVE_DEVICE error"
**Solution:**
- [ ] Did you disconnect and reconnect? (not just refresh)
- [ ] Did you wait 1-2 minutes after reconnecting?
- [ ] Do you have Spotify open on at least one device?
- [ ] Check browser console (F12) for errors

### "Permission denied" on reconnect
**Solution:**
- [ ] Clear browser cache completely
- [ ] Try incognito/private browsing window
- [ ] Make sure Spotify app is actually open on a device

### "Device modal doesn't appear"
**Solution:**
- [ ] Check you're on search page where play button exists
- [ ] Open browser console (F12) and look for errors
- [ ] Make sure Spotify is open on a device
- [ ] Try refreshing the page

### "Selected device but music won't play"
**Solution:**
- [ ] Make sure Spotify app is running on that device
- [ ] Try a different device
- [ ] Restart the Spotify app on that device
- [ ] Check if device is in private session (won't work)

---

## Why Device Must Be Active

Spotify's API **requires** at least one active device to control playback. This is a Spotify limitation, not our app.

**Active Device = Spotify app is open and connected to Spotify API**

When you open Spotify on any device:
1. Spotify connects to Spotify's servers
2. Server registers it as "available device"
3. You can see it in device list
4. You can send play commands to it

---

## Quick Checklist

- [ ] Spotify app open on at least one device
- [ ] Disconnected from the app
- [ ] Cleared browser cache
- [ ] Reconnected to Spotify
- [ ] Waited 1-2 minutes
- [ ] Searched for a song
- [ ] Clicked play button
- [ ] Selected device when prompted
- [ ] Music is playing ✅

---

## If All Else Fails

### Nuclear Option: Full Reset

```bash
# Stop server
# Ctrl+C

# Clear all session/cache data
rm -rf .django_cache
rm -f db.sqlite3  # WARNING: Deletes all data!

# Recreate database
python manage.py migrate

# Create new superuser
python manage.py createsuperuser

# Restart
python manage.py runserver
```

⚠️ **WARNING:** This deletes ALL data. Only do if testing locally!

---

## Important Notes

✅ **You do NOT need to:**
- Reinstall Spotify
- Delete the app
- Reset your computer
- Create new Spotify account

✅ **You only need to:**
1. Disconnect (1 click)
2. Clear cache (2 clicks)
3. Reconnect (1 click)
4. Authorize (1 click)

---

## Spotify Permission Dialog

When you reconnect, you'll see this:

```
SYRO WANTS ACCESS TO YOUR ACCOUNT

The app would like permission to:
✓ Read your currently playing track
✓ Control playback
✓ Access your library
✓ Manage playlists
... (other permissions)

[Agree]  [Don't Allow]
```

Click "Agree" to proceed. The new scopes will be visible here.

---

## After Re-Authorization

Your tokens will be **automatically updated** with the new scopes:
- Access token will include new permissions
- Refresh token will grant new permissions
- All playback commands will work ✅

---

## Expected Timeline

| Step | Time |
|------|------|
| Disconnect | < 1 sec |
| Clear cache | 1-2 min |
| Reconnect | < 1 sec |
| Authorize | < 1 sec |
| Wait for Spotify sync | 1-2 min |
| **Total** | **~5 min** |

---

## Still Stuck?

Check these in order:
1. **Browser console (F12)** - Look for JavaScript errors
2. **Django console** - Look for 401/403/404 errors
3. **Spotify app status** - Is it really open and connected?
4. **Network tab (F12)** - Check if API calls are failing

---

**Status:** Follow the steps above to fix!
**Time to Fix:** 5 minutes
**Difficulty:** Easy (3 clicks)

Once reconnected, the universal player will work perfectly! 🎵
