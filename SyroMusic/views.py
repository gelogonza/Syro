# SyroMusic/views.py

from django.shortcuts import render, redirect
from .models import Artist, Album, Song, Playlist
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from spotipy.oauth2 import SpotifyOAuth
from django.conf import settings

def artist_list(request):
    artists = Artist.objects.all()
    return render(request, 'SyroMusic/artist_list.html', {'artists': artists})

def album_list(request):
    albums = Album.objects.all()
    return render(request, 'SyroMusic/album_list.html', {'albums': albums})

def song_list(request):
    songs = Song.objects.all()
    return render(request, 'SyroMusic/song_list.html', {'songs': songs})

def playlist_list(request):
    playlists = Playlist.objects.all()
    return render(request, 'SyroMusic/playlist_list.html', {'playlists': playlists})

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # Redirect to the desired page after registration
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})

def spotify_login(request):
    # Initialize SpotifyOAuth with your Spotify API credentials
    sp_oauth = SpotifyOAuth(client_id=settings.SPOTIPY_CLIENT_ID,
                           client_secret=settings.SPOTIPY_CLIENT_SECRET,
                           redirect_uri=settings.SPOTIPY_REDIRECT_URI,
                           scope='user-library-read')  # Adjust the scope as needed

    # Redirect the user to Spotify's login page
    return redirect(sp_oauth.get_authorize_url())

def spotify_callback(request):
    # Initialize SpotifyOAuth with your Spotify API credentials
    sp_oauth = SpotifyOAuth(client_id=settings.SPOTIPY_CLIENT_ID,
                           client_secret=settings.SPOTIPY_CLIENT_SECRET,
                           redirect_uri=settings.SPOTIPY_REDIRECT_URI,
                           scope='user-library-read')  # Adjust the scope as needed

    # Get the authorization code from the request
    code = request.GET.get('code')

    # Exchange the authorization code for access tokens
    token_info = sp_oauth.get_access_token(code)
    
    if token_info:
        # Store the access token securely or associate it with the user's account
        access_token = token_info['access_token']
        # Implement your logic here for further actions after successful authentication

    # Redirect the user to the desired page after successful authentication
    return redirect('home')  # Replace 'home' with the name of your desired view
