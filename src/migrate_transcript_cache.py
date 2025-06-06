"""
Migration script to populate transcript cache with existing raw transcript files.

This script scans the data/raw/ directory for existing AssemblyAI transcript files
and populates the new transcript cache to avoid re-processing videos that already
have transcripts.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any

from .transcript_cache import TranscriptCacheManager
from .utils.logging_helper import LoggingMixin

logger = logging.getLogger(__name__)


class TranscriptCacheMigrator(LoggingMixin):
    """Migrates existing raw transcript files to the new transcript cache."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize migrator.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__()
        self.config = config
        self.transcript_cache = TranscriptCacheManager(config)
        self.raw_data_dir = Path('data/raw')
        
        # Set logging context
        self.set_logging_context({
            'component': 'TranscriptCacheMigrator'
        })

    def migrate_existing_transcripts(self) -> Dict[str, int]:
        """Migrate existing raw transcript files to transcript cache.
        
        Returns:
            Dictionary with migration statistics
        """
        stats = {
            'found': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': 0
        }
        
        if not self.raw_data_dir.exists():
            self.log_warning(f"Raw data directory not found: {self.raw_data_dir}")
            return stats
        
        # Find all AssemblyAI transcript files
        transcript_pattern = "transcript_*_assemblyai.json"
        transcript_files = list(self.raw_data_dir.glob(transcript_pattern))
        
        self.log_info(f"Found {len(transcript_files)} raw transcript files to migrate")
        stats['found'] = len(transcript_files)
        
        for transcript_file in transcript_files:
            try:
                # Extract video ID from filename
                # Format: transcript_{video_id}_assemblyai.json
                filename_parts = transcript_file.stem.split('_')
                if len(filename_parts) < 3:
                    self.log_warning(f"Unexpected filename format: {transcript_file.name}")
                    stats['errors'] += 1
                    continue
                
                video_id = '_'.join(filename_parts[1:-1])  # Handle video IDs with underscores
                
                # Check if already cached
                if self.transcript_cache.is_cached(video_id):
                    self.log_debug(f"Transcript already cached for {video_id}")
                    stats['skipped'] += 1
                    continue
                
                # Load raw transcript data
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                
                # Extract transcript text
                transcript_text = raw_data.get('text', '')
                if not transcript_text:
                    self.log_warning(f"No transcript text found in {transcript_file.name}")
                    stats['errors'] += 1
                    continue
                
                # Prepare metadata
                metadata = {
                    'migrated_from': str(transcript_file),
                    'original_data': raw_data
                }
                
                # Cache the transcript
                if self.transcript_cache.cache_transcript(video_id, transcript_text, metadata):
                    self.log_debug(f"Migrated transcript for {video_id}")
                    stats['migrated'] += 1
                else:
                    self.log_error(f"Failed to cache transcript for {video_id}")
                    stats['errors'] += 1
                
            except Exception as e:
                self.log_error(f"Error migrating {transcript_file.name}: {e}")
                stats['errors'] += 1
        
        self.log_info(f"Migration complete: {stats['migrated']} migrated, {stats['skipped']} skipped, {stats['errors']} errors")
        return stats

    def verify_migration(self) -> Dict[str, Any]:
        """Verify the migration by checking cache consistency.
        
        Returns:
            Dictionary with verification results
        """
        verification = {
            'cache_files': 0,
            'raw_files': 0,
            'matches': 0,
            'mismatches': []
        }
        
        # Get cache statistics
        cache_stats = self.transcript_cache.get_cache_stats()
        verification['cache_files'] = cache_stats['total_files']
        
        # Count raw transcript files
        if self.raw_data_dir.exists():
            raw_files = list(self.raw_data_dir.glob("transcript_*_assemblyai.json"))
            verification['raw_files'] = len(raw_files)
            
            # Check for matches
            for raw_file in raw_files:
                filename_parts = raw_file.stem.split('_')
                if len(filename_parts) >= 3:
                    video_id = '_'.join(filename_parts[1:-1])
                    
                    if self.transcript_cache.is_cached(video_id):
                        verification['matches'] += 1
                    else:
                        verification['mismatches'].append(video_id)
        
        return verification


def run_migration(config: Dict[str, Any]) -> None:
    """Run the transcript cache migration.
    
    Args:
        config: Configuration dictionary
    """
    migrator = TranscriptCacheMigrator(config)
    
    print("🔄 Starting transcript cache migration...")
    stats = migrator.migrate_existing_transcripts()
    
    print(f"📊 Migration Results:")
    print(f"  Found: {stats['found']} raw transcript files")
    print(f"  Migrated: {stats['migrated']} transcripts")
    print(f"  Skipped: {stats['skipped']} (already cached)")
    print(f"  Errors: {stats['errors']}")
    
    if stats['migrated'] > 0:
        print("\n🔍 Verifying migration...")
        verification = migrator.verify_migration()
        
        print(f"📋 Verification Results:")
        print(f"  Cache files: {verification['cache_files']}")
        print(f"  Raw files: {verification['raw_files']}")
        print(f"  Matches: {verification['matches']}")
        
        if verification['mismatches']:
            print(f"  Mismatches: {len(verification['mismatches'])}")
            for video_id in verification['mismatches'][:5]:
                print(f"    - {video_id}")
            if len(verification['mismatches']) > 5:
                print(f"    ... and {len(verification['mismatches']) - 5} more")
    
    print("✅ Migration complete!")


if __name__ == "__main__":
    import yaml
    
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    run_migration(config)
