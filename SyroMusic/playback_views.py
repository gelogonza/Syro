"""
Playback-related views for SyroMusic application.
Handles music playback, device management, and queue controls.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .models import (
    SpotifyDevice, NowPlaying, PlaybackQueue,
    SpotifyUser, UserListeningStats
)
from .services import SpotifyService, TokenManager


@login_required(login_url='login')
def player_page(request):
    """Main player page with interactive player UI."""
    try:
        spotify_user = SpotifyUser.objects.filter(user=request.user).first()
        if not spotify_user or not spotify_user.is_connected:
            messages.warning(request, 'Please connect your Spotify account to use the player.')
            return redirect('music:dashboard')

        # Refresh token if needed
        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            messages.error(request, 'Failed to refresh Spotify token. Please reconnect.')
            return redirect('music:dashboard')

        # Get current playback and devices
        sp = SpotifyService(access_token=access_token)
        current_playback = sp.get_current_playback()
        devices = sp.get_available_devices()

        # Get or create NowPlaying model
        now_playing, _ = NowPlaying.objects.get_or_create(user=request.user)

        # Update NowPlaying if there is active playback
        if current_playback and current_playback.get('item'):
            item = current_playback['item']
            now_playing.spotify_track_id = item.get('id', '')
            now_playing.track_name = item.get('name', '')
            now_playing.artist_name = ', '.join([a['name'] for a in item.get('artists', [])])
            now_playing.album_name = item.get('album', {}).get('name', '')
            now_playing.album_image_url = item.get('album', {}).get('images', [{}])[0].get('url', '')
            now_playing.spotify_track_url = item.get('external_urls', {}).get('spotify', '')
            now_playing.duration_ms = item.get('duration_ms', 0)
            now_playing.progress_ms = current_playback.get('progress_ms', 0)
            now_playing.is_playing = current_playback.get('is_playing', False)
            now_playing.is_explicit = item.get('explicit', False)

            if current_playback.get('device'):
                device_info = current_playback['device']
                device, _ = SpotifyDevice.objects.get_or_create(
                    user=request.user,
                    device_id=device_info['id'],
                    defaults={
                        'device_name': device_info['name'],
                        'device_type': device_info.get('type', 'Unknown'),
                    }
                )
                now_playing.device = device

            if current_playback.get('context'):
                context = current_playback['context']
                now_playing.context_type = context.get('type', '')
                now_playing.context_id = context.get('href', '').split('/')[-1]

            now_playing.save()

        # Get or create PlaybackQueue
        queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)

        context = {
            'spotify_user': spotify_user,
            'now_playing': now_playing,
            'current_playback': current_playback,
            'devices': devices,
            'queue': queue,
        }
        return render(request, 'SyroMusic/player.html', context)

    except Exception as e:
        messages.error(request, f'Error loading player: {str(e)}')
        return redirect('music:dashboard')


@login_required(login_url='login')
@require_http_methods(['POST'])
def play_track(request):
    """Play a specific track, album, or playlist."""
    import json
    
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            uri = data.get('track_uri') or data.get('uri')
            device_id = data.get('device_id')
        else:
            uri = request.POST.get('track_uri') or request.POST.get('uri')
            device_id = request.POST.get('device_id')

        if not uri:
            return JsonResponse({'status': 'error', 'message': 'URI required'}, status=400)

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)

        # Determine if this is a track URI or context URI (album/playlist)
        if 'track:' in uri:
            # Play single track
            success = sp.start_playback(uris=[uri], device_id=device_id)
        else:
            # Play context (album, playlist, artist, etc)
            success = sp.start_playback(context_uri=uri, device_id=device_id)

        if success:
            return JsonResponse({'status': 'success', 'message': 'Playing'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to start playback'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def play_pause(request):
    """Toggle play/pause."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        device_id = request.POST.get('device_id')

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)
        playback = sp.get_current_playback()

        if playback and playback.get('is_playing'):
            success = sp.pause_playback(device_id=device_id)
            message = 'Paused'
        else:
            success = sp.resume_playback(device_id=device_id)
            message = 'Playing'

        if success:
            return JsonResponse({'status': 'success', 'message': message})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to toggle playback'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def next_track(request):
    """Skip to next track."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        device_id = request.POST.get('device_id')

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)
        success = sp.next_track(device_id=device_id)

        if success:
            return JsonResponse({'status': 'success', 'message': 'Skipped to next track'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to skip'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def previous_track(request):
    """Go to previous track."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        device_id = request.POST.get('device_id')

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)
        success = sp.previous_track(device_id=device_id)

        if success:
            return JsonResponse({'status': 'success', 'message': 'Went to previous track'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to go to previous'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def seek(request):
    """Seek to position in current track."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        position_ms = request.POST.get('position_ms')
        device_id = request.POST.get('device_id')

        if not position_ms:
            return JsonResponse({'status': 'error', 'message': 'Position required'}, status=400)

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)
        success = sp.seek_to_position(int(position_ms), device_id=device_id)

        if success:
            return JsonResponse({'status': 'success', 'message': 'Seeked to position'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to seek'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def set_volume(request):
    """Set playback volume."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        volume = request.POST.get('volume')
        device_id = request.POST.get('device_id')

        if not volume:
            return JsonResponse({'status': 'error', 'message': 'Volume required'}, status=400)

        volume = int(volume)
        if not 0 <= volume <= 100:
            return JsonResponse({'status': 'error', 'message': 'Volume must be 0-100'}, status=400)

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)
        success = sp.set_volume(volume, device_id=device_id)

        if success:
            return JsonResponse({'status': 'success', 'message': 'Volume set'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to set volume'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def transfer_playback(request):
    """Transfer playback to another device."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        device_id = request.POST.get('device_id')

        if not device_id:
            return JsonResponse({'status': 'error', 'message': 'Device ID required'}, status=400)

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)
        success = sp.transfer_playback(device_id, play=True)

        if success:
            return JsonResponse({'status': 'success', 'message': 'Transferred playback'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to transfer playback'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def set_shuffle(request):
    """Toggle shuffle mode."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        state = request.POST.get('state', 'false').lower() == 'true'
        device_id = request.POST.get('device_id')

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)
        success = sp.set_shuffle(state, device_id=device_id)

        # Update local queue
        queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)
        queue.shuffle_enabled = state
        queue.save()

        if success:
            status = 'enabled' if state else 'disabled'
            return JsonResponse({'status': 'success', 'message': f'Shuffle {status}'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to set shuffle'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def set_repeat(request):
    """Set repeat mode."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        mode = request.POST.get('mode', 'off')
        device_id = request.POST.get('device_id')

        if mode not in ['off', 'context', 'track']:
            return JsonResponse({'status': 'error', 'message': 'Invalid repeat mode'}, status=400)

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        sp = SpotifyService(access_token=access_token)
        success = sp.set_repeat(mode, device_id=device_id)

        # Update local queue
        queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)
        queue.repeat_mode = mode
        queue.save()

        if success:
            messages = {
                'off': 'Repeat off',
                'context': 'Repeat all enabled',
                'track': 'Repeat one enabled'
            }
            return JsonResponse({'status': 'success', 'message': messages[mode]})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to set repeat'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
def get_playback_state(request):
    """Get current playback state (AJAX endpoint)."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        access_token = TokenManager.refresh_user_token(spotify_user)

        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token expired'}, status=401)

        sp = SpotifyService(access_token=access_token)
        playback = sp.get_current_playback()

        if not playback:
            return JsonResponse({'status': 'no_playback'})

        device_info = playback.get('device', {})
        item = playback.get('item', {})

        # Extract album image URL
        album_images = item.get('album', {}).get('images', []) if item else []
        album_image_url = album_images[0].get('url', '') if album_images else ''

        return JsonResponse({
            'status': 'success',
            'is_playing': playback.get('is_playing', False),
            'progress_ms': playback.get('progress_ms', 0),
            'duration_ms': item.get('duration_ms', 0) if item else 0,
            'track_name': item.get('name', '') if item else '',
            'artist_name': ', '.join([a['name'] for a in item.get('artists', [])]) if item else '',
            'album_name': item.get('album', {}).get('name', '') if item else '',
            'album_image_url': album_image_url,
            'device_name': device_info.get('name', ''),
            'device_type': device_info.get('type', ''),
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
def get_available_devices(request):
    """Get list of available devices for playback (AJAX endpoint)."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        access_token = TokenManager.refresh_user_token(spotify_user)

        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token expired'}, status=401)

        sp = SpotifyService(access_token=access_token)
        devices = sp.get_available_devices()

        if not devices:
            return JsonResponse({
                'status': 'success',
                'devices': [],
                'has_active_device': False,
                'message': 'No devices available. Open Spotify on a device to make it available.'
            })

        device_list = []
        active_device = None

        for device in devices:
            device_data = {
                'id': device.get('id', ''),
                'name': device.get('name', 'Unknown Device'),
                'type': device.get('type', 'Unknown'),
                'is_active': device.get('is_active', False),
                'is_private_session': device.get('is_private_session', False),
                'supports_volume': device.get('supports_volume', True),
                'volume_percent': device.get('volume_percent', 100),
            }
            device_list.append(device_data)

            if device.get('is_active'):
                active_device = device_data

        return JsonResponse({
            'status': 'success',
            'devices': device_list,
            'active_device': active_device,
            'has_active_device': bool(active_device),
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def add_to_queue(request):
    """Add a track to the playback queue."""
    import json
    
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        
        # Handle both JSON and form data
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            track_uri = data.get('track_uri') or data.get('uri')
            track_info = data.get('track_info', {})
        else:
            track_uri = request.POST.get('track_uri') or request.POST.get('uri')
            track_info = {}

        if not track_uri:
            return JsonResponse({'status': 'error', 'message': 'Track URI required'}, status=400)

        access_token = TokenManager.refresh_user_token(spotify_user)
        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token refresh failed'}, status=401)

        # Add to Spotify's queue
        sp = SpotifyService(access_token=access_token)
        success = sp.add_to_queue(track_uri)

        if success:
            # Also update local queue model
            queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)
            
            # Add track to queue_tracks list
            if not queue.queue_tracks:
                queue.queue_tracks = []
            
            # Create track object with info
            track_obj = {
                'uri': track_uri,
                'spotify_id': track_uri.split(':')[-1] if ':' in track_uri else track_uri,
                'added_at': timezone.now().isoformat(),
            }
            
            # Merge with provided track info
            if track_info:
                track_obj.update(track_info)
            
            queue.queue_tracks.append(track_obj)
            queue.save()

            track_name = track_info.get('title', 'Track')
            return JsonResponse({
                'status': 'success',
                'message': f'"{track_name}" added to queue',
                'queue_length': len(queue.queue_tracks)
            })
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to add to queue'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
def get_queue(request):
    """Get the current playback queue."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        access_token = TokenManager.refresh_user_token(spotify_user)

        if not access_token:
            return JsonResponse({'status': 'error', 'message': 'Token expired'}, status=401)

        # Get Spotify's queue
        sp = SpotifyService(access_token=access_token)
        spotify_queue = sp.get_queue()

        # Get local queue
        local_queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)

        # Format queue data
        queue_items = []
        
        if spotify_queue and 'queue' in spotify_queue:
            for item in spotify_queue['queue']:
                queue_items.append({
                    'id': item.get('id', ''),
                    'uri': item.get('uri', ''),
                    'name': item.get('name', 'Unknown'),
                    'artists': ', '.join([a['name'] for a in item.get('artists', [])]),
                    'album': item.get('album', {}).get('name', ''),
                    'album_image': item.get('album', {}).get('images', [{}])[0].get('url', ''),
                    'duration_ms': item.get('duration_ms', 0),
                })

        return JsonResponse({
            'status': 'success',
            'currently_playing': spotify_queue.get('currently_playing') if spotify_queue else None,
            'queue': queue_items,
            'queue_length': len(queue_items),
            'local_queue_length': len(local_queue.queue_tracks),
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def clear_queue(request):
    """Clear the local queue."""
    try:
        queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)
        queue.queue_tracks = []
        queue.current_index = 0
        queue.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Queue cleared'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
