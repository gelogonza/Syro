# Step-by-Step: Fix "No Active Device" Error

## 🎯 Quick Fix (5 minutes)

### Step 1️⃣: Disconnect Spotify
```
1. Go to: http://localhost:8000/music/dashboard/
2. Look for "Disconnect Spotify" button (usually red/orange)
3. Click it
4. Confirm when asked
```

**What you'll see:**
```
✅ Spotify disconnected
You'll be redirected to login page
```

---

### Step 2️⃣: Clear Browser Cache
```
Windows/Linux:
  Press: Ctrl + Shift + Delete

Mac:
  Press: Cmd + Shift + Delete
```

**What to clear:**
```
☑ Cookies and other site data
☑ Cached images and files
Time range: All time

Click: Clear data
```

**Then:**
```
Close ALL browser tabs with your app
Close ALL Spotify browser windows
```

---

### Step 3️⃣: Reconnect to Spotify
```
1. Go to: http://localhost:8000/
2. Click "Connect with Spotify" button
3. You'll see Spotify login page
```

**Login with your Spotify credentials:**
```
Username: your_spotify_email
Password: your_spotify_password
```

---

### Step 4️⃣: Authorize New Permissions
```
Spotify will show a permissions screen:

SYRO WANTS ACCESS TO YOUR ACCOUNT

Permissions include:
✓ Read your profile
✓ Read your email
✓ READ WHAT YOU'RE PLAYING (NEW! 🆕)
✓ CONTROL PLAYBACK (NEW! 🆕)
✓ Access your saved tracks
✓ Manage your playlists
... more permissions

Click: [Agree]
```

⚠️ **Important:** Make sure to click "Agree" to grant all permissions!

---

### Step 5️⃣: Wait for Sync
```
After clicking Agree, you'll see:

"Syncing your Spotify data..."

Wait 1-2 minutes for sync to complete.
You'll see your dashboard load.
```

---

### Step 6️⃣: Test Playback
```
1. Make sure Spotify is OPEN on your computer/phone
   (Just having the app running is enough)

2. Go to: http://localhost:8000/music/search/

3. Search for any song (e.g., "Blinding Lights")

4. Click the "▶ PLAY" button on a Spotify result

5. You should see a device selector or music starts playing!
```

✅ **If music plays, you're done!**

---

## ✅ Verification Checklist

After reconnecting, verify:

- [ ] You're logged in to the app
- [ ] Your Spotify profile shows on dashboard
- [ ] Search page works
- [ ] Play button appears on tracks
- [ ] Clicking play shows device selector or plays immediately
- [ ] Toast notification appears ("Now playing...")
- [ ] Music actually plays on your device

---

## 🐛 If It Still Doesn't Work

### Check 1: Is Spotify Running?
```
Your device must have Spotify open!

✅ Do this:
  - Open Spotify app on your computer
  - Or open Spotify on your phone
  - OR both

❌ Don't do this:
  - Just closed Spotify
  - Spotify running in background but paused
```

### Check 2: Is Spotify Connected?
```
✅ Spotify is connected when:
  - App shows "Now Playing: ..." at top
  - You can see your username
  - Device shows in your device list

❌ Spotify is NOT connected when:
  - App is open but shows offline
  - Says "Connect to Spotify"
  - Device not in device list
```

### Check 3: Browser Console Errors
```
Press F12 to open Developer Tools
Click "Console" tab
Look for red error messages

Common errors and fixes:
- "CSRF token missing" → Refresh page, try again
- "No active device" → Open Spotify on a device
- "401 Unauthorized" → Reconnect to Spotify
```

### Check 4: Check Django Logs
```
Look at Django server output in terminal:

❌ If you see:
  ERROR HTTP Error for PUT to https://api.spotify.com/...
  Player command failed: No active device found

✅ Then:
  - Open Spotify on a device
  - Try playing again

If error persists after opening Spotify:
  - Go back to Step 1 (disconnect/reconnect)
```

---

## 📱 Device Types That Work

✅ **These will appear in device selector:**
- Desktop/Laptop (Windows, Mac, Linux)
- Smartphone (iPhone, Android with Spotify app)
- Tablet (iPad, Android tablets)
- Smart Speaker (Echo, Google Home, HomePod)
- Smart TV (Apple TV, Android TV)

❌ **These won't work:**
- Web browser (spotify.com) - doesn't count as device
- Closed Spotify app
- Spotify in offline mode
- Device in private session

---

## 🎵 Once It's Working

You can now:

✅ Play from **Search page** - search for song, click play
✅ Play from **Playlists** - coming soon (we'll add this)
✅ Play from **Artist pages** - coming soon (we'll add this)
✅ Play from **Album pages** - coming soon (we'll add this)
✅ Device selector shows automatically
✅ Music plays on any device you choose

---

## 🆘 Still Need Help?

Read: [AUTHORIZATION_FIX.md](AUTHORIZATION_FIX.md)

That file has:
- Detailed troubleshooting
- Database cleanup options
- Advanced solutions
- FAQ section

---

## 📋 Summary

| Step | Action | Time |
|------|--------|------|
| 1 | Disconnect | 30 sec |
| 2 | Clear cache | 1 min |
| 3 | Reconnect | 30 sec |
| 4 | Authorize | 30 sec |
| 5 | Wait | 1-2 min |
| 6 | Test | 1 min |
| **Total** | **Done!** | **5 min** |

---

## 🚀 You're All Set!

Once you've completed these steps, the universal player will work perfectly.

**Next:** Go play some music! 🎵

---

**Last Updated:** 2025-10-29
**Status:** Ready to follow
