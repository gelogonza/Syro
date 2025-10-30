#!/usr/bin/env python
"""
Test script to verify Spotify OAuth setup is correct.
Run this to debug any authorization issues.
"""

import os
import sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Syro.settings')

import django
django.setup()

from django.conf import settings
from SyroMusic.services import SpotifyService
from SyroMusic.models import SpotifyUser
from django.contrib.auth.models import User

print("=" * 70)
print("SPOTIFY OAUTH SETUP TEST")
print("=" * 70)
print()

# Test 1: Check environment variables
print("1. CHECKING ENVIRONMENT VARIABLES")
print("-" * 70)

client_id = settings.SPOTIPY_CLIENT_ID
client_secret = settings.SPOTIPY_CLIENT_SECRET
redirect_uri = settings.SPOTIPY_REDIRECT_URI

checks = [
    ("Client ID", client_id),
    ("Client Secret", client_secret),
    ("Redirect URI", redirect_uri),
]

for name, value in checks:
    if value:
        if name == "Client Secret":
            display = value[:10] + "..." + value[-5:]
        else:
            display = value
        print(f"[PASS] {name}: {display}")
    else:
        print(f"[FAIL] {name}: NOT SET")
        sys.exit(1)

print()

# Test 2: Generate authorization URL
print("2. GENERATING AUTHORIZATION URL")
print("-" * 70)

try:
    auth_url = SpotifyService.get_authorization_url()
    print(f"[PASS] Auth URL generated successfully")
    print(f"   Length: {len(auth_url)} characters")

    # Extract scopes from URL
    import urllib.parse
    parsed = urllib.parse.urlparse(auth_url)
    params = urllib.parse.parse_qs(parsed.query)
    scopes = params.get('scope', [''])[0].split()

    print(f"   Scopes: {len(scopes)} total")
    for scope in scopes:
        print(f"      [PASS] {scope}")

    print()
except Exception as e:
    print(f"[FAIL] Error: {e}")
    sys.exit(1)

# Test 3: Check SpotifyUser database
print("3. CHECKING SPOTIFY USER DATABASE")
print("-" * 70)

spotify_users = SpotifyUser.objects.all()
if spotify_users.exists():
    print(f"[PASS] Found {spotify_users.count()} Spotify user(s):")
    for su in spotify_users:
        print(f"   - {su.user.username}: is_connected={su.is_connected}")
else:
    print(f"[INFO]  No Spotify users yet (this is OK - they'll be created on first auth)")

print()

# Test 4: Check user accounts
print("4. CHECKING USER ACCOUNTS")
print("-" * 70)

users = User.objects.all()
if users.exists():
    print(f"[PASS] Found {users.count()} user(s):")
    for user in users:
        has_spotify = hasattr(user, 'spotify_user')
        status = "[PASS] Has Spotify" if has_spotify else "[WARN]  No Spotify yet"
        print(f"   - {user.username}: {status}")
else:
    print(f"[FAIL] No users found - need to create users first")

print()

# Test 5: OAuth flow summary
print("5. OAUTH FLOW SUMMARY")
print("-" * 70)

print("""
When you click "Connect with Spotify":

1. You're sent to:
   https://accounts.spotify.com/authorize?...

2. Spotify may show:
   - Login page (if not logged in)
   - Agreement page (SYRO WANTS ACCESS)
   - Or both, or neither (optimized flow)

3. You click [Agree]

4. You're redirected to:
   http://localhost:8000/music/spotify/callback/

   With auth code in URL like:
   http://localhost:8000/music/spotify/callback/?code=AQC...

5. Backend exchanges code for tokens

6. You're logged in! [PASS]
""")

print()

# Final status
print("=" * 70)
print("FINAL STATUS")
print("=" * 70)

all_good = (
    client_id and
    client_secret and
    redirect_uri and
    len(scopes) >= 15  # Should have at least 15 scopes
)

if all_good:
    print("[PASS] SETUP IS CORRECT!")
    print()
    print("Next steps:")
    print("1. Go to: http://localhost:8000/music/dashboard/")
    print("2. Click 'Connect with Spotify'")
    print("3. You may or may not see login/agreement pages")
    print("   (Spotify optimizes by skipping if you're logged in)")
    print("4. After redirecting back, check your profile appears")
    print("5. Go to search and try playing a song!")
    print()
else:
    print("[FAIL] SETUP HAS ISSUES - See errors above")
    sys.exit(1)

print("=" * 70)
