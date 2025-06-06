"""
Audio Cache Manager for SetupSpawn Shorts Scraper.

Manages local audio file caching for reliable transcription processing.
"""

import json
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .utils.logging_helper import LoggingMixin
from .exceptions import AudioCacheError


class AudioCacheManager(LoggingMixin):
    """Manages local audio file caching for transcription."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize audio cache manager.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config
        
        # Cache configuration
        cache_config = config.get('audio_cache', {})
        self.cache_dir = Path(cache_config.get('cache_dir', 'data/audio_cache'))
        self.audio_format = cache_config.get('audio_format', 'wav')
        self.max_cache_size_gb = cache_config.get('max_cache_size_gb', 5.0)
        self.cleanup_after_days = cache_config.get('cleanup_after_days', 30)
        self.keep_successful_transcripts = cache_config.get('keep_successful_transcripts', True)
        
        # Cache index file
        self.cache_index_file = self.cache_dir / 'cache_index.json'
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Load or create cache index
        self._cache_index = self._load_cache_index()
        
        # Set logging context
        self.set_logging_context({
            'component': 'AudioCacheManager',
            'cache_dir': str(self.cache_dir)
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
        
        return {
            'created_at': datetime.now().isoformat(),
            'last_cleanup': datetime.now().isoformat(),
            'files': {}
        }

    def _save_cache_index(self) -> None:
        """Save cache index to file."""
        try:
            with open(self.cache_index_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache_index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log_error(f"Failed to save cache index: {e}")

    def get_audio_path(self, video_id: str) -> Path:
        """Get the expected audio file path for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to audio file
        """
        return self.cache_dir / f"{video_id}.{self.audio_format}"

    def get_metadata_path(self, video_id: str) -> Path:
        """Get the metadata file path for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to metadata file
        """
        return self.cache_dir / f"{video_id}.metadata.json"

    def is_cached(self, video_id: str) -> bool:
        """Check if audio is already cached for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if audio is cached, False otherwise
        """
        audio_path = self.get_audio_path(video_id)
        metadata_path = self.get_metadata_path(video_id)
        
        # Check if both files exist and are in index
        if audio_path.exists() and metadata_path.exists():
            if video_id in self._cache_index['files']:
                return True
        
        # Clean up orphaned entries
        if video_id in self._cache_index['files']:
            self.log_warning(f"Removing orphaned cache entry for {video_id}")
            del self._cache_index['files'][video_id]
            self._save_cache_index()
        
        return False

    def add_to_cache(self, video_id: str, audio_path: Path, metadata: Dict[str, Any]) -> bool:
        """Add audio file to cache.
        
        Args:
            video_id: YouTube video ID
            audio_path: Path to audio file to cache
            metadata: Audio metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            target_audio_path = self.get_audio_path(video_id)
            target_metadata_path = self.get_metadata_path(video_id)
            
            # Copy audio file to cache
            if audio_path != target_audio_path:
                shutil.copy2(audio_path, target_audio_path)
            
            # Save metadata
            with open(target_metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Update cache index
            self._cache_index['files'][video_id] = {
                'cached_at': datetime.now().isoformat(),
                'file_size': target_audio_path.stat().st_size,
                'format': self.audio_format,
                'transcription_status': 'pending',
                'last_accessed': datetime.now().isoformat()
            }
            
            self._save_cache_index()
            self.log_info(f"Added {video_id} to audio cache")
            return True
            
        except Exception as e:
            self.log_error(f"Failed to add {video_id} to cache: {e}")
            return False

    def get_cached_audio(self, video_id: str) -> Optional[Path]:
        """Get cached audio file path.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to cached audio file or None if not cached
        """
        if not self.is_cached(video_id):
            return None
        
        audio_path = self.get_audio_path(video_id)
        
        # Update last accessed time
        if video_id in self._cache_index['files']:
            self._cache_index['files'][video_id]['last_accessed'] = datetime.now().isoformat()
            self._save_cache_index()
        
        return audio_path

    def get_cached_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get cached audio metadata.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Audio metadata dictionary or None if not cached
        """
        if not self.is_cached(video_id):
            return None
        
        metadata_path = self.get_metadata_path(video_id)
        
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.log_error(f"Failed to load metadata for {video_id}: {e}")
            return None

    def update_transcription_status(self, video_id: str, status: str) -> None:
        """Update transcription status for cached audio.
        
        Args:
            video_id: YouTube video ID
            status: Transcription status ('pending', 'success', 'failed')
        """
        if video_id in self._cache_index['files']:
            self._cache_index['files'][video_id]['transcription_status'] = status
            self._cache_index['files'][video_id]['last_accessed'] = datetime.now().isoformat()
            self._save_cache_index()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_files = len(self._cache_index['files'])
        total_size = sum(
            entry.get('file_size', 0) 
            for entry in self._cache_index['files'].values()
        )
        
        # Count by status
        status_counts = {}
        for entry in self._cache_index['files'].values():
            status = entry.get('transcription_status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            'total_files': total_files,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'total_size_gb': round(total_size / (1024 * 1024 * 1024), 3),
            'status_counts': status_counts,
            'cache_dir': str(self.cache_dir),
            'max_size_gb': self.max_cache_size_gb
        }

    def cleanup_cache(self, force: bool = False) -> Dict[str, Any]:
        """Clean up old cache files.

        Args:
            force: Force cleanup regardless of time since last cleanup

        Returns:
            Dictionary with cleanup results
        """
        try:
            if not self._should_cleanup(force):
                return {'skipped': True, 'reason': 'Recent cleanup'}

            files_to_remove = self._identify_cleanup_candidates()
            results = self._remove_cache_files(files_to_remove)
            self._update_cleanup_timestamp()

            self.log_info(f"Cache cleanup completed: {results['files_removed']} files removed, "
                         f"{results['space_freed_mb']:.2f} MB freed")

            return results

        except Exception as e:
            error_msg = f"Cache cleanup failed: {e}"
            self.log_error(error_msg)
            raise AudioCacheError(error_msg)

    def _should_cleanup(self, force: bool) -> bool:
        """Check if cleanup should be performed.

        Args:
            force: Force cleanup regardless of time since last cleanup

        Returns:
            True if cleanup should be performed, False otherwise
        """
        if force:
            return True

        last_cleanup = datetime.fromisoformat(self._cache_index.get('last_cleanup', '1970-01-01'))
        return (datetime.now() - last_cleanup).days >= 1

    def _identify_cleanup_candidates(self) -> List[str]:
        """Identify files that should be removed during cleanup.

        Returns:
            List of video IDs to remove
        """
        cutoff_date = datetime.now() - timedelta(days=self.cleanup_after_days)
        files_to_remove = []

        for video_id, entry in self._cache_index['files'].items():
            cached_at = datetime.fromisoformat(entry['cached_at'])
            transcription_status = entry.get('transcription_status', 'pending')

            # Remove if old and not successful (if keep_successful_transcripts is True)
            should_remove = cached_at < cutoff_date
            if self.keep_successful_transcripts and transcription_status == 'success':
                should_remove = False

            if should_remove:
                files_to_remove.append(video_id)

        return files_to_remove

    def _remove_cache_files(self, files_to_remove: List[str]) -> Dict[str, Any]:
        """Remove cache files and update index.

        Args:
            files_to_remove: List of video IDs to remove

        Returns:
            Dictionary with removal results
        """
        cleanup_results = {
            'files_removed': 0,
            'space_freed_mb': 0,
            'errors': []
        }

        for video_id in files_to_remove:
            try:
                file_size = self._remove_single_cache_entry(video_id)
                cleanup_results['files_removed'] += 1
                cleanup_results['space_freed_mb'] += file_size / (1024 * 1024)

            except Exception as e:
                error_msg = f"Failed to remove {video_id}: {e}"
                cleanup_results['errors'].append(error_msg)
                self.log_error(error_msg)

        return cleanup_results

    def _remove_single_cache_entry(self, video_id: str) -> int:
        """Remove a single cache entry and return freed space.

        Args:
            video_id: Video ID to remove

        Returns:
            Total file size removed in bytes
        """
        audio_path = self.get_audio_path(video_id)
        metadata_path = self.get_metadata_path(video_id)

        file_size = 0
        if audio_path.exists():
            file_size += audio_path.stat().st_size
            audio_path.unlink()

        if metadata_path.exists():
            file_size += metadata_path.stat().st_size
            metadata_path.unlink()

        # Remove from index
        if video_id in self._cache_index['files']:
            del self._cache_index['files'][video_id]

        return file_size

    def _update_cleanup_timestamp(self) -> None:
        """Update the last cleanup timestamp in the cache index."""
        self._cache_index['last_cleanup'] = datetime.now().isoformat()
        self._save_cache_index()
