#!/usr/bin/env python
"""
Script to clean up and reset Spotify authorization.
This deletes the old Spotify connection so you can reconnect with new scopes.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Syro.settings')
django.setup()

from django.contrib.auth.models import User
from SyroMusic.models import SpotifyUser

print("=" * 70)
print("SPOTIFY AUTHORIZATION CLEANUP")
print("=" * 70)
print()

# Find all users with Spotify accounts
users_with_spotify = User.objects.filter(spotify_user__isnull=False)

if not users_with_spotify:
    print("✅ No Spotify accounts found. You're all set to reconnect!")
    exit(0)

print(f"Found {users_with_spotify.count()} user(s) with Spotify accounts:")
print()

for user in users_with_spotify:
    spotify_user = user.spotify_user
    print(f"  👤 {user.username}")
    print(f"     Spotify ID: {spotify_user.spotify_id}")
    print(f"     Is Connected: {spotify_user.is_connected}")
    print(f"     Token Expires: {spotify_user.token_expires_at}")
    print()

# Ask for confirmation
confirm = input("Delete all Spotify connections to allow fresh reconnect? (yes/no): ").strip().lower()

if confirm != 'yes':
    print("❌ Cancelled. No changes made.")
    exit(0)

# Delete all Spotify connections
count = SpotifyUser.objects.count()
SpotifyUser.objects.all().delete()

print()
print(f"✅ Successfully deleted {count} Spotify connection(s)")
print()
print("Next steps:")
print("1. Go to: http://localhost:8000/music/dashboard/")
print("2. Click 'Connect with Spotify'")
print("3. Authorize with NEW permissions")
print("4. Wait 1-2 minutes for sync")
print("5. Try playing music!")
print()
