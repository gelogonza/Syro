# music/models.py

from django.db import models
from django.contrib.auth.models import User

class Artist(models.Model):
    name = models.CharField(max_length=255)
    biography = models.TextField()
    # Other artist-related fields (e.g., image, genre)

class Album(models.Model):
    title = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE)
    release_date = models.DateField()
    # Other album-related fields (e.g., cover image)

class Song(models.Model):
    title = models.CharField(max_length=255)
    album = models.ForeignKey(Album, on_delete=models.CASCADE)
    duration = models.DurationField()
    # Other song-related fields (e.g., track number, genre)

class Playlist(models.Model):
    title = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    songs = models.ManyToManyField(Song)
    # Other playlist-related fields (e.g., description)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Additional user-related fields (e.g., profile picture, bio)
