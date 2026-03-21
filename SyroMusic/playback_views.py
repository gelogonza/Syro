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

        # Get current playback and devices
        sp = SpotifyService(spotify_user)
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
        return render(request, 'syromusic/player.html', context)

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

        sp = SpotifyService(spotify_user)

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
        device_id = request.POST.get('device_id') or None

        sp = SpotifyService(spotify_user)
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
        device_id = request.POST.get('device_id') or None

        sp = SpotifyService(spotify_user)
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
        device_id = request.POST.get('device_id') or None

        sp = SpotifyService(spotify_user)
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
        device_id = request.POST.get('device_id') or None

        if position_ms is None:
            return JsonResponse({'status': 'error', 'message': 'Position required'}, status=400)

        sp = SpotifyService(spotify_user)
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
        device_id = request.POST.get('device_id') or None

        if volume is None:
            return JsonResponse({'status': 'error', 'message': 'Volume required'}, status=400)

        volume = int(volume)
        if not 0 <= volume <= 100:
            return JsonResponse({'status': 'error', 'message': 'Volume must be 0-100'}, status=400)

        sp = SpotifyService(spotify_user)
        success = sp.set_volume(volume, device_id=device_id)

        if success:
            return JsonResponse({'status': 'success', 'message': 'Volume set'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Failed to set volume'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def set_shuffle(request):
    """Toggle shuffle mode."""
    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        state = request.POST.get('state', 'false').lower() == 'true'
        device_id = request.POST.get('device_id') or None

        sp = SpotifyService(spotify_user)
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
        device_id = request.POST.get('device_id') or None

        if mode not in ['off', 'context', 'track']:
            return JsonResponse({'status': 'error', 'message': 'Invalid repeat mode'}, status=400)

        sp = SpotifyService(spotify_user)
        success = sp.set_repeat(mode, device_id=device_id)

        # Update local queue
        queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)
        queue.repeat_mode = mode
        queue.save()

        if success:
            repeat_messages = {
                'off': 'Repeat off',
                'context': 'Repeat all enabled',
                'track': 'Repeat one enabled',
            }
            return JsonResponse({'status': 'success', 'message': repeat_messages[mode]})
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

        sp = SpotifyService(spotify_user)
        playback = sp.get_current_playback()

        if not playback:
            return JsonResponse({'status': 'no_playback'})

        device_info = playback.get('device', {})
        item = playback.get('item', {})
        context = playback.get('context') or {}

        # Extract album image URL
        album_images = item.get('album', {}).get('images', []) if item else []
        album_image_url = album_images[0].get('url', '') if album_images else ''

        return JsonResponse({
            'status': 'success',
            'is_playing': playback.get('is_playing', False),
            'progress_ms': playback.get('progress_ms', 0),
            'duration_ms': item.get('duration_ms', 0) if item else 0,
            'track_name': item.get('name', '') if item else '',
            'track_uri': item.get('uri', '') if item else '',
            'track_id': item.get('id', '') if item else '',
            'artist_name': ', '.join([a['name'] for a in item.get('artists', [])]) if item else '',
            'artist_ids': [a.get('id', '') for a in item.get('artists', [])] if item else [],
            'album_name': item.get('album', {}).get('name', '') if item else '',
            'album_uri': item.get('album', {}).get('uri', '') if item else '',
            'album_image_url': album_image_url,
            'context_type': context.get('type', ''),
            'context_uri': context.get('uri', ''),
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

        sp = SpotifyService(spotify_user)
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

        sp = SpotifyService(spotify_user)
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

            # Merge with provided track info (only if it's a dict)
            if track_info and isinstance(track_info, dict):
                track_obj.update(track_info)
            
            queue.queue_tracks.append(track_obj)
            queue.save(update_fields=['queue_tracks', 'last_updated'])

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
        sp = SpotifyService(spotify_user)
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
        queue.save(update_fields=['queue_tracks', 'current_index', 'last_updated'])

        return JsonResponse({
            'status': 'success',
            'message': 'Queue cleared'
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_devices(request):
    """Get available Spotify devices."""
    try:
        spotify_user = SpotifyUser.objects.get(user=request.user)
        service = SpotifyService(spotify_user)

        logger.info(f"Fetching devices for user {request.user.username}")
        devices = service.get_available_devices()

        if not devices:
            logger.warning("No devices data returned from Spotify")
            return Response({'devices': []}, status=200)

        logger.info(f"Found {len(devices)} devices: {[d.get('name') for d in devices]}")

        return Response({'devices': devices}, status=200)

    except SpotifyUser.DoesNotExist:
        logger.error(f"No SpotifyUser found for {request.user.username}")
        return Response(
            {'error': 'Spotify account not connected'},
            status=400
        )
    except Exception as e:
        logger.error(f"Error fetching devices: {str(e)}", exc_info=True)
        return Response(
            {'error': f'Failed to fetch devices: {str(e)}'},
            status=500
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def transfer_playback(request):
    """Transfer playback to a specific device (accepts JSON or form data)."""
    try:
        # DRF request.data parses both JSON and form-encoded bodies
        device_id = (request.data.get('device_id') or '').strip() or None
        if not device_id:
            return Response({'status': 'error', 'message': 'device_id is required'}, status=400)

        spotify_user = SpotifyUser.objects.get(user=request.user)
        service = SpotifyService(spotify_user)

        logger.info(f"Attempting to transfer playback to device: {device_id}")
        success = service.transfer_playback(device_id)  # force_play defaults to True

        if success:
            logger.info(f"Successfully transferred playback to device: {device_id}")
            return Response({'status': 'success', 'message': 'Transferred playback'}, status=200)
        else:
            logger.error(f"Failed to transfer playback to device: {device_id}")
            return Response({'status': 'error', 'message': 'Failed to transfer playback'}, status=400)

    except SpotifyUser.DoesNotExist:
        return Response({'status': 'error', 'message': 'Spotify account not connected'}, status=400)
    except Exception as e:
        logger.error(f"Error transferring playback: {str(e)}", exc_info=True)
        return Response({'status': 'error', 'message': str(e)}, status=500)


@login_required(login_url='login')
@require_http_methods(['POST'])
def autoplay_next(request):
    """
    Called when a track ends with no queued content.
    Priority order:
      1. Local queue has tracks → Spotify has already queued them; just skip to next.
      2. Was playing in an album/playlist context → skip to next (Spotify handles it).
      3. Single-track playback → queue 3 Spotify recommendations then skip.
    """
    import json as _json

    try:
        spotify_user = get_object_or_404(SpotifyUser, user=request.user)
        sp = SpotifyService(spotify_user)

        body = {}
        if request.content_type and 'application/json' in request.content_type:
            try:
                body = _json.loads(request.body)
            except Exception:
                pass

        # 1. Local queue has tracks → skip so Spotify plays the next queued track
        queue, _ = PlaybackQueue.objects.get_or_create(user=request.user)
        if queue.queue_tracks:
            success = sp.next_track()
            if success:
                return JsonResponse({'status': 'success', 'message': 'Playing next queued track'})

        # 2. Get current playback to decide strategy
        playback = sp.get_current_playback()
        context = (playback or {}).get('context') or {}
        item = (playback or {}).get('item') or {}

        # Playing in an album/playlist context → skip to next; Spotify auto-advances
        if context.get('type') in ('album', 'playlist', 'artist'):
            success = sp.next_track()
            if success:
                context_label = context.get('type', 'context').capitalize()
                return JsonResponse({
                    'status': 'success',
                    'message': f'Continuing {context_label}',
                })

        # 3. Single track → fetch recommendations and queue them
        seed_tracks = [item['id']] if item.get('id') else []
        seed_artists = [item['artists'][0]['id']] if item.get('artists') else []

        if not seed_tracks and not seed_artists:
            return JsonResponse({'status': 'no_playback', 'message': 'Nothing playing'})

        recs = sp.get_recommendations(
            seed_tracks=seed_tracks[:1] or None,
            seed_artists=seed_artists[:1] if not seed_tracks else None,
            limit=3,
        )

        tracks = (recs or {}).get('tracks', [])
        if not tracks:
            return JsonResponse({'status': 'info', 'message': 'No recommendations available'})

        queued = 0
        for track in tracks:
            track_uri = track.get('uri', '')
            if track_uri and sp.add_to_queue(track_uri):
                queued += 1

        if queued:
            sp.next_track()
            return JsonResponse({
                'status': 'success',
                'message': f'Autoplaying {queued} recommended track{"s" if queued != 1 else ""}',
            })

        return JsonResponse({'status': 'info', 'message': 'Autoplay not available'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
