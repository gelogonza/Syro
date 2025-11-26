"""
Centralized error handling utilities for SyroApp.
Provides consistent error responses and user-friendly messages.
"""

import logging
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class APIError:
    """Standardized API error response builder."""

    @staticmethod
    def success(data=None, message="Success", status_code=status.HTTP_200_OK):
        """Build a success response."""
        return Response(
            {
                "status": "success",
                "message": message,
                "data": data,
            },
            status=status_code,
        )

    @staticmethod
    def error(
        message="An error occurred",
        error_code="UNKNOWN_ERROR",
        status_code=status.HTTP_400_BAD_REQUEST,
        details=None,
    ):
        """Build an error response."""
        response_data = {
            "status": "error",
            "message": message,
            "error_code": error_code,
        }
        if details:
            response_data["details"] = details

        return Response(response_data, status=status_code)

    @staticmethod
    def not_found(resource_name="Resource"):
        """Build a 404 not found response."""
        return APIError.error(
            message=f"{resource_name} not found",
            error_code="NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    @staticmethod
    def unauthorized(message="Authentication required"):
        """Build a 401 unauthorized response."""
        return APIError.error(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    @staticmethod
    def forbidden(message="You don't have permission to access this resource"):
        """Build a 403 forbidden response."""
        return APIError.error(
            message=message,
            error_code="FORBIDDEN",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    @staticmethod
    def invalid_request(message="Invalid request", details=None):
        """Build a 400 bad request response."""
        return APIError.error(
            message=message,
            error_code="INVALID_REQUEST",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
        )

    @staticmethod
    def server_error(message="An internal server error occurred", error_id=None):
        """Build a 500 server error response."""
        logger.error(f"Internal server error: {message} (ID: {error_id})")
        return APIError.error(
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    @staticmethod
    def spotify_error(message="Spotify API error", details=None):
        """Build a Spotify-specific error response."""
        logger.error(f"Spotify API error: {message}")
        return APIError.error(
            message=message,
            error_code="SPOTIFY_API_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


class UserFriendlyMessages:
    """User-friendly error and success messages."""

    # Spotify Connection
    SPOTIFY_NOT_CONNECTED = "Please connect your Spotify account first."
    SPOTIFY_DISCONNECTED = "Your Spotify account has been disconnected."
    SPOTIFY_AUTH_FAILED = "Failed to authenticate with Spotify. Please try again."

    # Playback
    NO_DEVICES_AVAILABLE = (
        "No active Spotify devices found. Please open Spotify on a device."
    )
    PLAYBACK_FAILED = "Failed to start playback. Please try again."
    PLAYBACK_NO_TRACK = "No track selected. Please search for a song first."

    # Search & Discovery
    SEARCH_NO_RESULTS = "No tracks found matching your search. Try a different query."
    SEARCH_INVALID_QUERY = "Search query must be at least 2 characters long."

    # The Crate (Color Discovery)
    CRATE_SYNC_START = "Starting album sync... This may take a few minutes."
    CRATE_SYNC_COMPLETE = (
        "Albums synced successfully! Colors will be extracted automatically."
    )
    CRATE_NO_ALBUMS = "No albums found. Try syncing your Spotify library."

    # Sonic Aura
    SONIC_AURA_NO_TRACKS = "Not enough listening history. Keep listening to generate your vibe!"
    SONIC_AURA_GENERATED = "Your Sonic Aura has been generated!"

    # The Frequency
    FREQUENCY_DISCOVER_COMPLETE = "Found a track! Add to queue or play now."
    FREQUENCY_NO_RECOMMENDATIONS = "No recommendations found for this combination."

    # Playlists
    PLAYLIST_CREATED = "Playlist created successfully!"
    PLAYLIST_DELETED = "Playlist deleted."
    PLAYLIST_SONG_ADDED = "Song added to playlist!"
    PLAYLIST_SONG_REMOVED = "Song removed from playlist."


class LoggingMixin:
    """Mixin for consistent logging in views."""

    def log_action(self, action, details=None):
        """Log an action with user context."""
        user = self.request.user if hasattr(self, "request") else "unknown"
        message = f"[{user}] {action}"
        if details:
            message += f" | {details}"
        logger.info(message)

    def log_error(self, action, error):
        """Log an error with user context."""
        user = self.request.user if hasattr(self, "request") else "unknown"
        logger.error(f"[{user}] {action} | Error: {str(error)}", exc_info=True)

    def log_warning(self, action, warning):
        """Log a warning with user context."""
        user = self.request.user if hasattr(self, "request") else "unknown"
        logger.warning(f"[{user}] {action} | Warning: {warning}")
