"""
Phase 1: Video Discovery

Uses yt-dlp to discover YouTube Shorts from SetupSpawn channel.
"""

import logging
from typing import List, Dict, Any, Optional

from .db import DatabaseManager
from .clients import YouTubeClient
from .utils import FileManager, DataValidator
from .utils.logging_helper import LoggingMixin
from .exceptions import VideoDiscoveryError, ValidationError

logger = logging.getLogger(__name__)


class VideoDiscoverer(LoggingMixin):
    """Discovers YouTube Shorts from SetupSpawn channel."""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """Initialize video discoverer.

        Args:
            db_manager: Database manager instance
            config: Configuration dictionary
        """
        super().__init__()
        self.db_manager = db_manager
        self.config = config

        # Initialize clients and utilities
        self.youtube_client = YouTubeClient(config)
        self.file_manager = FileManager()
        self.validator = DataValidator()

        # Configuration
        self.since_date = config['youtube'].get('since_date')

        # Set logging context
        self.set_logging_context({
            'component': 'VideoDiscoverer',
            'channel': config['youtube'].get('channel_name', 'Unknown')
        })
    
    def discover_videos(self) -> List[Dict[str, Any]]:
        """Discover new YouTube Shorts from the channel.

        Returns:
            List of discovered video metadata

        Raises:
            VideoDiscoveryError: If discovery fails
        """
        self.log_info("Starting video discovery")

        if not self.youtube_client.is_configured():
            raise VideoDiscoveryError("YouTube client not configured")

        try:
            # Get channel videos
            channel_videos = self.youtube_client.discover_channel_videos()

            if not channel_videos:
                self.log_warning("No videos found in channel")
                return []

            # Process each video
            discovered_videos = []
            for video_data in channel_videos:
                processed_video = self._process_video(video_data)
                if processed_video:
                    discovered_videos.append(processed_video)

            self.log_info(f"Discovery complete: {len(discovered_videos)} new videos found")
            return discovered_videos

        except Exception as e:
            raise VideoDiscoveryError(f"Failed to discover videos: {str(e)}")

    def _process_video(self, video_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single video for discovery.

        Args:
            video_data: Raw video data from YouTube client

        Returns:
            Processed video data or None if video should be skipped
        """
        try:
            # Validate video data
            video_data = self.validator.validate_video_data(video_data)
            video_id = video_data['id']

            # Check if it's a Short
            if not self._is_short_video(video_data):
                self.log_debug(f"Skipping {video_id}: not a Short")
                return None

            # Check date filter
            if not self._is_video_recent(video_data):
                self.log_debug(f"Skipping {video_id}: older than {self.since_date}")
                return None

            # Try to insert into database
            if self._insert_video_to_db(video_data):
                self.log_info(f"Discovered new video: {video_id} - {video_data['title']}")
                self._save_raw_metadata(video_id, video_data.get('raw_info', {}))
                return video_data
            else:
                self.log_debug(f"Video already exists: {video_id}")
                return None

        except ValidationError as e:
            self.log_warning(f"Invalid video data: {e}")
            return None
        except Exception as e:
            video_id = video_data.get('id', 'unknown')
            self.log_error(f"Failed to process video {video_id}: {e}")
            return None

    def _is_short_video(self, video_data: Dict[str, Any]) -> bool:
        """Check if video is a YouTube Short (≤60 seconds).

        Args:
            video_data: Video data dictionary

        Returns:
            True if video is a Short
        """
        duration = video_data.get('duration', 0)
        return duration <= 60

    def _is_video_recent(self, video_data: Dict[str, Any]) -> bool:
        """Check if video is newer than the since_date filter.

        Args:
            video_data: Video data dictionary

        Returns:
            True if video should be processed
        """
        if not self.since_date:
            return True

        published_date = video_data.get('published_at', '')
        return published_date >= self.since_date

    def _insert_video_to_db(self, video_data: Dict[str, Any]) -> bool:
        """Insert video into database.

        Args:
            video_data: Validated video data

        Returns:
            True if video was inserted (new), False if already exists
        """
        return self.db_manager.insert_video(
            video_data['id'],
            video_data['title'],
            video_data['published_at']
        )

    def _save_raw_metadata(self, video_id: str, metadata: Dict[str, Any]):
        """Save raw video metadata to file.

        Args:
            video_id: YouTube video ID
            metadata: Raw metadata from YouTube API
        """
        try:
            file_path = f"data/raw/discover_{video_id}.json"
            self.file_manager.save_json(metadata, file_path)
            self.log_debug(f"Saved raw metadata for {video_id}")

        except Exception as e:
            self.log_error(f"Failed to save raw metadata for {video_id}: {e}")
    
    def get_pending_videos(self) -> List[Dict[str, Any]]:
        """Get videos that need processing.
        
        Returns:
            List of videos with 'new' status
        """
        return self.db_manager.get_videos_by_status('new')
