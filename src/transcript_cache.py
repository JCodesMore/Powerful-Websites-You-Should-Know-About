"""
Transcript Cache Manager

Manages local caching of AssemblyAI transcript responses to avoid unnecessary API calls
and improve processing speed for subsequent runs.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .utils.logging_helper import LoggingMixin

logger = logging.getLogger(__name__)


class TranscriptCacheManager(LoggingMixin):
    """Manages local transcript caching for AssemblyAI responses."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize transcript cache manager.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config
        
        # Cache configuration
        cache_config = config.get('transcript_cache', {})
        self.cache_dir = Path(cache_config.get('cache_dir', 'data/transcript_cache'))
        self.cleanup_after_days = cache_config.get('cleanup_after_days', 90)
        self.max_cache_size_mb = cache_config.get('max_cache_size_mb', 100)
        
        # Cache index file
        self.cache_index_file = self.cache_dir / 'cache_index.json'
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize cache index
        self._cache_index = self._load_cache_index()
        
        # Set logging context
        self.set_logging_context({
            'component': 'TranscriptCacheManager'
        })

    def _load_cache_index(self) -> Dict[str, Any]:
        """Load cache index from file.
        
        Returns:
            Cache index dictionary
        """
        if self.cache_index_file.exists():
            try:
                with open(self.cache_index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.log_warning(f"Failed to load cache index: {e}")
        
        # Return default index structure
        return {
            'created_at': datetime.now().isoformat(),
            'last_cleanup': None,
            'files': {}
        }

    def _save_cache_index(self):
        """Save cache index to file."""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_error(f"Failed to save cache index: {e}")

    def get_transcript_path(self, video_id: str) -> Path:
        """Get path to cached transcript file.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to transcript cache file
        """
        return self.cache_dir / f"{video_id}.json"

    def is_cached(self, video_id: str) -> bool:
        """Check if transcript is already cached for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if transcript is cached, False otherwise
        """
        transcript_path = self.get_transcript_path(video_id)
        
        # Check if file exists and is in index
        if transcript_path.exists():
            if video_id in self._cache_index['files']:
                return True
        
        # Clean up orphaned entries
        if video_id in self._cache_index['files']:
            self.log_warning(f"Removing orphaned transcript cache entry for {video_id}")
            del self._cache_index['files'][video_id]
            self._save_cache_index()
        
        return False

    def get_cached_transcript(self, video_id: str) -> Optional[str]:
        """Get cached transcript text.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Cached transcript text or None if not cached
        """
        if not self.is_cached(video_id):
            return None
        
        transcript_path = self.get_transcript_path(video_id)
        
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update last accessed time
            if video_id in self._cache_index['files']:
                self._cache_index['files'][video_id]['last_accessed'] = datetime.now().isoformat()
                self._save_cache_index()
            
            # Return transcript text
            return data.get('text', '')
            
        except Exception as e:
            self.log_error(f"Failed to load cached transcript for {video_id}: {e}")
            return None

    def cache_transcript(self, video_id: str, transcript_text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Cache transcript data for a video.
        
        Args:
            video_id: YouTube video ID
            transcript_text: Transcript text from AssemblyAI
            metadata: Optional metadata about the transcript
            
        Returns:
            True if successful, False otherwise
        """
        try:
            transcript_path = self.get_transcript_path(video_id)
            
            # Prepare transcript data
            transcript_data = {
                'text': transcript_text,
                'cached_at': datetime.now().isoformat(),
                'source': 'assemblyai',
                'metadata': metadata or {}
            }
            
            # Save transcript file
            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(transcript_data, f, indent=2, ensure_ascii=False)
            
            # Update cache index
            self._cache_index['files'][video_id] = {
                'cached_at': datetime.now().isoformat(),
                'file_size': transcript_path.stat().st_size,
                'last_accessed': datetime.now().isoformat(),
                'source': 'assemblyai'
            }
            
            self._save_cache_index()
            self.log_info(f"Cached transcript for {video_id}")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to cache transcript for {video_id}: {e}")
            return False

    def cache_transcript_with_timing(self, video_id: str, transcript_data: Dict[str, Any]) -> bool:
        """Cache full transcript data including timing information.

        Args:
            video_id: YouTube video ID
            transcript_data: Full transcript data with timing from AssemblyAI

        Returns:
            True if successful, False otherwise
        """
        try:
            transcript_path = self.get_transcript_path(video_id)

            # Prepare enhanced transcript data
            enhanced_data = {
                'text': transcript_data.get('text', ''),
                'words': transcript_data.get('words', []),
                'confidence': transcript_data.get('confidence'),
                'audio_duration': transcript_data.get('audio_duration'),
                'cached_at': datetime.now().isoformat(),
                'source': 'assemblyai',
                'has_timing': bool(transcript_data.get('words'))
            }

            # Save transcript file with timing data
            with open(transcript_path, 'w', encoding='utf-8') as f:
                json.dump(enhanced_data, f, indent=2, ensure_ascii=False)

            # Update cache index
            self._cache_index['files'][video_id] = {
                'cached_at': datetime.now().isoformat(),
                'file_size': transcript_path.stat().st_size,
                'last_accessed': datetime.now().isoformat(),
                'source': 'assemblyai',
                'has_timing': bool(transcript_data.get('words'))
            }

            self._save_cache_index()
            self.log_info(f"Cached transcript with timing for {video_id}")
            return True

        except Exception as e:
            self.log_error(f"Failed to cache transcript with timing for {video_id}: {e}")
            return False

    def get_cached_transcript_with_timing(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get cached transcript data including timing information.

        Args:
            video_id: YouTube video ID

        Returns:
            Full transcript data with timing or None if not cached
        """
        if not self.is_cached(video_id):
            return None

        transcript_path = self.get_transcript_path(video_id)

        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Update last accessed time
            if video_id in self._cache_index['files']:
                self._cache_index['files'][video_id]['last_accessed'] = datetime.now().isoformat()
                self._save_cache_index()

            # Return full transcript data
            return data

        except Exception as e:
            self.log_error(f"Failed to load cached transcript with timing for {video_id}: {e}")
            return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_files = len(self._cache_index['files'])
        total_size = 0
        
        for video_id in self._cache_index['files']:
            transcript_path = self.get_transcript_path(video_id)
            if transcript_path.exists():
                total_size += transcript_path.stat().st_size
        
        return {
            'total_files': total_files,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir),
            'created_at': self._cache_index.get('created_at'),
            'last_cleanup': self._cache_index.get('last_cleanup')
        }

    def cleanup_old_transcripts(self) -> int:
        """Clean up old transcript cache files.
        
        Returns:
            Number of files cleaned up
        """
        if self.cleanup_after_days <= 0:
            return 0
        
        cleaned_count = 0
        cutoff_date = datetime.now().timestamp() - (self.cleanup_after_days * 24 * 60 * 60)
        
        for video_id in list(self._cache_index['files'].keys()):
            file_info = self._cache_index['files'][video_id]
            cached_at = datetime.fromisoformat(file_info['cached_at']).timestamp()
            
            if cached_at < cutoff_date:
                transcript_path = self.get_transcript_path(video_id)
                try:
                    if transcript_path.exists():
                        transcript_path.unlink()
                    del self._cache_index['files'][video_id]
                    cleaned_count += 1
                    self.log_debug(f"Cleaned up old transcript cache for {video_id}")
                except Exception as e:
                    self.log_error(f"Failed to clean up transcript cache for {video_id}: {e}")
        
        if cleaned_count > 0:
            self._cache_index['last_cleanup'] = datetime.now().isoformat()
            self._save_cache_index()
            self.log_info(f"Cleaned up {cleaned_count} old transcript cache files")
        
        return cleaned_count

    def clear_cache(self) -> bool:
        """Clear all cached transcripts.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove all transcript files
            for transcript_file in self.cache_dir.glob("*.json"):
                if transcript_file != self.cache_index_file:
                    transcript_file.unlink()
            
            # Reset cache index
            self._cache_index = {
                'created_at': datetime.now().isoformat(),
                'last_cleanup': datetime.now().isoformat(),
                'files': {}
            }
            self._save_cache_index()
            
            self.log_info("Cleared all transcript cache files")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to clear transcript cache: {e}")
            return False
