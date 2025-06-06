"""
Phase 2: Transcript Extraction

Extracts transcripts using youtube-transcript-api (primary) and AssemblyAI (fallback).
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .db import DatabaseManager
from .clients import YouTubeClient, AssemblyAIClient
from .utils import FileManager, DataValidator
from .utils.logging_helper import LoggingMixin
from .exceptions import ValidationError
from .audio_cache import AudioCacheManager
from .transcript_cache import TranscriptCacheManager

logger = logging.getLogger(__name__)


class TranscriptExtractor(LoggingMixin):
    """Extracts transcripts from YouTube videos."""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """Initialize transcript extractor.

        Args:
            db_manager: Database manager instance
            config: Configuration dictionary
        """
        super().__init__()
        self.db_manager = db_manager
        self.config = config

        # Initialize clients and utilities
        self.youtube_client = YouTubeClient(config)  # Now used for audio download
        self.assemblyai_client = AssemblyAIClient(config)
        self.file_manager = FileManager()
        self.validator = DataValidator()
        self.audio_cache = AudioCacheManager(config)
        self.transcript_cache = TranscriptCacheManager(config)

        # Set logging context
        self.set_logging_context({
            'component': 'TranscriptExtractor'
        })
    
    def extract_transcript(self, video_id: str) -> bool:
        """Extract transcript for a video using AssemblyAI exclusively.

        Args:
            video_id: YouTube video ID

        Returns:
            True if successful, False otherwise

        Raises:
            TranscriptError: If transcript extraction fails
        """
        try:
            # Validate video ID
            self.validator.validate_video_id(video_id)
            self.log_info(f"Extracting transcript for video: {video_id}")

            # Use AssemblyAI for transcription (YouTube doesn't provide transcripts for Shorts)
            transcript_text = self._try_assemblyai_transcript(video_id)

            # Process result
            if transcript_text:
                return self._save_transcript_success(video_id, transcript_text)
            else:
                return self._handle_transcript_failure(video_id, "No transcript available from AssemblyAI")

        except ValidationError as e:
            return self._handle_transcript_failure(video_id, f"Invalid video ID: {e}")
        except Exception as e:
            return self._handle_transcript_failure(video_id, f"Transcript extraction failed: {str(e)}")



    def _try_assemblyai_transcript(self, video_id: str) -> Optional[str]:
        """Try to get transcript using AssemblyAI with local audio and transcript caching.

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript text or None if not available
        """
        if not self.assemblyai_client.is_configured():
            self.log_warning("AssemblyAI not configured")
            return None

        try:
            # Check if transcript is already cached
            if self.transcript_cache.is_cached(video_id):
                cached_transcript = self.transcript_cache.get_cached_transcript(video_id)
                if cached_transcript:
                    self.log_info(f"Using cached transcript for {video_id}")
                    return cached_transcript

            # Check if audio is already cached
            cached_audio_path = self.audio_cache.get_cached_audio(video_id)

            if cached_audio_path:
                self.log_info(f"Using cached audio for {video_id}")
                audio_path = cached_audio_path
            else:
                # Download audio locally
                audio_path = self._download_audio_locally(video_id)
                if not audio_path:
                    self.log_error(f"Failed to download audio for {video_id}")
                    return None

            # Transcribe with AssemblyAI using local file with timing data
            transcript_data = self.assemblyai_client.transcribe_local_audio_with_timing(str(audio_path))

            if transcript_data:
                transcript_text = transcript_data['text']  # Extract text for backward compatibility
                self.log_info(f"Got AssemblyAI transcript with timing for {video_id}")

                # Cache the full transcript data including timing
                self.transcript_cache.cache_transcript_with_timing(video_id, transcript_data)

                # Save raw transcript with timing data
                self._save_raw_transcript(video_id, transcript_data, 'assemblyai')

                # Store in database with timing data
                self.db_manager.update_video_transcript_data(video_id, transcript_data)

                # Update cache status to success
                self.audio_cache.update_transcription_status(video_id, 'success')

                return transcript_text  # Return text for backward compatibility
            else:
                # Update cache status to failed
                self.audio_cache.update_transcription_status(video_id, 'failed')
                return None

        except Exception as e:
            self.log_error(f"AssemblyAI transcription error for {video_id}: {e}")
            # Update cache status to failed
            try:
                self.audio_cache.update_transcription_status(video_id, 'failed')
            except:
                pass  # Don't let cache update errors mask the original error
            return None

    def _download_audio_locally(self, video_id: str) -> Optional[Path]:
        """Download audio file locally and add to cache.

        Args:
            video_id: YouTube video ID

        Returns:
            Path to downloaded audio file or None if failed
        """
        try:
            temp_audio_path = self._create_temp_audio_path(video_id)
            downloaded_path = self._download_audio_file(video_id, temp_audio_path)

            if not downloaded_path:
                return None

            metadata = self._get_audio_metadata_safe(video_id)
            return self._add_to_cache_and_cleanup(video_id, downloaded_path, metadata)

        except Exception as e:
            self.log_error(f"Audio download failed for {video_id}: {e}")
            return None

    def _create_temp_audio_path(self, video_id: str) -> Path:
        """Create temporary audio file path.

        Args:
            video_id: YouTube video ID

        Returns:
            Path for temporary audio file
        """
        import tempfile

        temp_dir = Path(tempfile.gettempdir()) / "setupspawn_audio"
        temp_dir.mkdir(exist_ok=True)
        return temp_dir / f"{video_id}_temp.wav"

    def _download_audio_file(self, video_id: str, temp_path: Path) -> Optional[Path]:
        """Download audio file using YouTube client.

        Args:
            video_id: YouTube video ID
            temp_path: Temporary file path

        Returns:
            Path to downloaded file or None if failed
        """
        downloaded_path = self.youtube_client.download_audio(video_id, temp_path)

        if not downloaded_path or not downloaded_path.exists():
            self.log_error(f"Audio download failed for {video_id}")
            return None

        return downloaded_path

    def _get_audio_metadata_safe(self, video_id: str) -> Dict[str, Any]:
        """Get audio metadata with fallback.

        Args:
            video_id: YouTube video ID

        Returns:
            Audio metadata dictionary
        """
        try:
            metadata = self.youtube_client.get_audio_metadata(video_id)
            if metadata:
                return metadata
        except Exception as e:
            self.log_warning(f"Failed to get metadata for {video_id}: {e}")

        # Fallback metadata
        import time
        return {
            'video_id': video_id,
            'downloaded_at': time.time(),
            'source': 'youtube_download'
        }

    def _add_to_cache_and_cleanup(self, video_id: str, downloaded_path: Path, metadata: Dict[str, Any]) -> Optional[Path]:
        """Add audio to cache and cleanup temporary files.

        Args:
            video_id: YouTube video ID
            downloaded_path: Path to downloaded audio file
            metadata: Audio metadata

        Returns:
            Path to cached audio file or fallback path
        """
        if self.audio_cache.add_to_cache(video_id, downloaded_path, metadata):
            self.log_info(f"Added {video_id} to audio cache")
            self._cleanup_temp_file(downloaded_path, video_id)
            return self.audio_cache.get_audio_path(video_id)
        else:
            self.log_error(f"Failed to add {video_id} to cache")
            return downloaded_path  # Return temp path as fallback

    def _cleanup_temp_file(self, downloaded_path: Path, video_id: str) -> None:
        """Clean up temporary audio file.

        Args:
            downloaded_path: Path to temporary file
            video_id: YouTube video ID
        """
        try:
            if downloaded_path != self.audio_cache.get_audio_path(video_id):
                downloaded_path.unlink()
        except Exception:
            pass  # Don't fail if cleanup fails

    def _save_transcript_success(self, video_id: str, transcript_text: str) -> bool:
        """Save successful transcript extraction.

        Args:
            video_id: YouTube video ID
            transcript_text: Extracted transcript text

        Returns:
            True
        """
        try:
            # Validate transcript
            validated_text = self.validator.validate_transcript(transcript_text)

            # Update database
            self._update_video_transcript(video_id, validated_text)
            self.db_manager.update_video_status(video_id, 'transcribed')

            self.log_info(f"Successfully extracted transcript for {video_id}")
            return True

        except ValidationError as e:
            return self._handle_transcript_failure(video_id, f"Invalid transcript: {e}")
        except Exception as e:
            return self._handle_transcript_failure(video_id, f"Failed to save transcript: {e}")

    def _handle_transcript_failure(self, video_id: str, error_msg: str) -> bool:
        """Handle transcript extraction failure.

        Args:
            video_id: YouTube video ID
            error_msg: Error message

        Returns:
            False
        """
        self.log_error(f"Failed to extract transcript for {video_id}: {error_msg}")
        self.db_manager.update_video_status(video_id, 'transcript_error', error_msg)
        return False
    
    def _save_raw_transcript(self, video_id: str, transcript_data: Dict[str, Any], source: str):
        """Save raw transcript data to file.

        Args:
            video_id: YouTube video ID
            transcript_data: Raw transcript data
            source: Source of transcript (youtube/assemblyai)
        """
        try:
            file_path = f"data/raw/transcript_{video_id}_{source}.json"
            self.file_manager.save_json(transcript_data, file_path)
            self.log_debug(f"Saved raw transcript for {video_id} from {source}")

        except Exception as e:
            self.log_error(f"Failed to save raw transcript for {video_id}: {e}")
    
    def _update_video_transcript(self, video_id: str, transcript_text: str):
        """Update video record with transcript text.

        Args:
            video_id: YouTube video ID
            transcript_text: Extracted transcript text
        """
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    UPDATE videos
                    SET transcript = ?
                    WHERE id = ?
                """, (transcript_text, video_id))
                conn.commit()
        except Exception as e:
            self.log_error(f"Failed to update transcript for {video_id}: {e}")

    def get_transcribed_videos(self) -> List[Dict[str, Any]]:
        """Get videos that have been transcribed.

        Returns:
            List of videos with 'transcribed' status
        """
        return self.db_manager.get_videos_by_status('transcribed')
