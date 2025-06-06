"""
CLI interface for SetupSpawn Shorts Scraper using Typer.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional
import yaml

import typer
from typer import Typer

from .db import DatabaseManager
from .discover import VideoDiscoverer
from .transcript import TranscriptExtractor
from .parse import TextParser
from .vision import VisionAnalyzer
from .export import TipsExporter
from .audio_cache import AudioCacheManager

# Create the main CLI app
app = Typer(
    name="setupspawn-scraper",
    help="SetupSpawn Shorts Scraper - Extract website tips from YouTube Shorts",
    add_completion=False
)

# Global variables for components
db_manager = None
config = None


def setup_logging(level: str = "INFO"):
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('data/exports/scraper.log', mode='a')
        ]
    )


def load_config() -> dict:
    """Load configuration from config.yaml."""
    config_path = Path("config.yaml")
    if not config_path.exists():
        typer.echo("Error: config.yaml not found", err=True)
        raise typer.Exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Expand environment variables
        import os
        for key, value in config.get('api_keys', {}).items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                config['api_keys'][key] = os.getenv(env_var, '')
        
        return config
    except Exception as e:
        typer.echo(f"Error loading config: {e}", err=True)
        raise typer.Exit(1)


def initialize_components():
    """Initialize global components."""
    global db_manager, config
    
    config = load_config()
    setup_logging(config.get('logging', {}).get('level', 'INFO'))
    
    # Initialize database
    db_path = config.get('database', {}).get('db_path', 'data/processed.db')
    db_manager = DatabaseManager(db_path)


@app.command()
def run(
    skip: Optional[List[str]] = typer.Option(
        None, 
        "--skip", 
        help="Phases to skip (discover,transcript,parse,vision,export)"
    ),
    since: Optional[str] = typer.Option(
        None, 
        "--since", 
        help="Only process videos since this date (YYYY-MM-DD)"
    ),
    limit: Optional[int] = typer.Option(
        None, 
        "--limit", 
        help="Maximum number of videos to process"
    ),
    dry_run: bool = typer.Option(
        False, 
        "--dry-run", 
        help="Show what would be done without making changes"
    )
):
    """Run the complete scraping pipeline."""
    initialize_components()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting SetupSpawn Shorts scraper pipeline")
    
    # Parse skip phases
    skip_phases = set(skip) if skip else set()
    
    # Update config with CLI options
    if since:
        config['youtube']['since_date'] = since
    if limit:
        config['youtube']['max_videos'] = limit
    if dry_run:
        config['development']['dry_run'] = True
    
    try:
        # Phase 1: Discovery
        if 'discover' not in skip_phases:
            typer.echo("🔍 Phase 1: Discovering videos...")
            discoverer = VideoDiscoverer(db_manager, config)
            videos = discoverer.discover_videos()
            typer.echo(f"   Found {len(videos)} new videos")
        
        # Phase 2: Transcription
        if 'transcript' not in skip_phases:
            typer.echo("📝 Phase 2: Extracting transcripts...")
            transcriber = TranscriptExtractor(db_manager, config)
            pending_videos = db_manager.get_videos_by_status('new')
            
            success_count = 0
            for video in pending_videos:
                if transcriber.extract_transcript(video['id']):
                    success_count += 1
            
            typer.echo(f"   Transcribed {success_count}/{len(pending_videos)} videos")
        
        # Phase 3: Parsing
        if 'parse' not in skip_phases:
            typer.echo("🤖 Phase 3: Parsing with gpt-4.1-mini...")
            parser = TextParser(db_manager, config)
            transcribed_videos = db_manager.get_videos_by_status('transcribed')
            
            success_count = 0
            for video in transcribed_videos:
                if parser.parse_transcript(video['id']):
                    success_count += 1
            
            typer.echo(f"   Parsed {success_count}/{len(transcribed_videos)} videos")
        
        # Phase 4: Vision Analysis
        if 'vision' not in skip_phases:
            typer.echo("👁️ Phase 4: Vision analysis...")
            analyzer = VisionAnalyzer(db_manager, config)
            parsed_videos = db_manager.get_videos_by_status('parsed')
            
            success_count = 0
            for video in parsed_videos:
                if analyzer.analyze_video(video['id']):
                    success_count += 1
            
            typer.echo(f"   Analyzed {success_count}/{len(parsed_videos)} videos")
        
        # Phase 5: Export
        if 'export' not in skip_phases:
            typer.echo("📊 Phase 5: Exporting to CSV...")
            exporter = TipsExporter(db_manager, config)
            if exporter.export_tips():
                typer.echo("   ✅ Export completed successfully")
            else:
                typer.echo("   ❌ Export failed")
        
        typer.echo("🎉 Pipeline completed successfully!")
        
    except KeyboardInterrupt:
        typer.echo("\n⚠️ Pipeline interrupted by user")
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"❌ Pipeline failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def resume():
    """Resume processing from where it left off."""
    initialize_components()
    
    logger = logging.getLogger(__name__)
    logger.info("Resuming scraper pipeline")
    
    try:
        # Check what needs to be done
        new_videos = db_manager.get_videos_by_status('new')
        transcribed_videos = db_manager.get_videos_by_status('transcribed')
        parsed_videos = db_manager.get_videos_by_status('parsed')
        
        total_pending = len(new_videos) + len(transcribed_videos) + len(parsed_videos)
        
        if total_pending == 0:
            typer.echo("✅ No pending work found. All videos are up to date.")
            return
        
        typer.echo(f"📋 Found {total_pending} videos needing processing:")
        typer.echo(f"   - {len(new_videos)} need transcription")
        typer.echo(f"   - {len(transcribed_videos)} need parsing")
        typer.echo(f"   - {len(parsed_videos)} need vision analysis")
        
        # Resume from transcription
        if new_videos:
            typer.echo("📝 Resuming transcription...")
            transcriber = TranscriptExtractor(db_manager, config)
            for video in new_videos:
                transcriber.extract_transcript(video['id'])
        
        # Resume from parsing
        transcribed_videos = db_manager.get_videos_by_status('transcribed')
        if transcribed_videos:
            typer.echo("🤖 Resuming parsing...")
            parser = TextParser(db_manager, config)
            for video in transcribed_videos:
                parser.parse_transcript(video['id'])
        
        # Resume from vision analysis
        parsed_videos = db_manager.get_videos_by_status('parsed')
        if parsed_videos:
            typer.echo("👁️ Resuming vision analysis...")
            analyzer = VisionAnalyzer(db_manager, config)
            for video in parsed_videos:
                analyzer.analyze_video(video['id'])
        
        # Export results
        typer.echo("📊 Exporting results...")
        exporter = TipsExporter(db_manager, config)
        exporter.export_tips()
        
        typer.echo("🎉 Resume completed successfully!")
        
    except Exception as e:
        typer.echo(f"❌ Resume failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def rerun(
    video: str = typer.Argument(..., help="Video ID to reprocess"),
    steps: str = typer.Option(
        "transcript,parse,vision", 
        "--steps", 
        help="Steps to rerun (comma-separated)"
    )
):
    """Re-process a specific video."""
    initialize_components()
    
    logger = logging.getLogger(__name__)
    logger.info(f"Rerunning steps for video: {video}")
    
    step_list = [s.strip() for s in steps.split(',')]
    
    try:
        # Validate video exists
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM videos WHERE id = ?", (video,))
            if not cursor.fetchone():
                typer.echo(f"❌ Video {video} not found in database", err=True)
                raise typer.Exit(1)
        
        typer.echo(f"🔄 Rerunning steps for video {video}: {', '.join(step_list)}")
        
        # Rerun specified steps
        if 'transcript' in step_list:
            typer.echo("📝 Re-extracting transcript...")
            transcriber = TranscriptExtractor(db_manager, config)
            transcriber.extract_transcript(video)
        
        if 'parse' in step_list:
            typer.echo("🤖 Re-parsing with gpt-4.1-mini...")
            parser = TextParser(db_manager, config)
            parser.reparse_video(video)
        
        if 'vision' in step_list:
            typer.echo("👁️ Re-analyzing with vision...")
            analyzer = VisionAnalyzer(db_manager, config)
            analyzer.analyze_video(video)
        
        typer.echo("✅ Rerun completed successfully!")
        
    except Exception as e:
        typer.echo(f"❌ Rerun failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def status():
    """Show pipeline status and statistics."""
    initialize_components()
    
    try:
        # Get status counts
        with db_manager.get_connection() as conn:
            cursor = conn.execute("""
                SELECT status, COUNT(*) 
                FROM videos 
                GROUP BY status
            """)
            status_counts = dict(cursor.fetchall())
            
            cursor = conn.execute("SELECT COUNT(*) FROM tips")
            total_tips = cursor.fetchone()[0]
        
        typer.echo("📊 SetupSpawn Scraper Status")
        typer.echo("=" * 30)
        
        for status, count in status_counts.items():
            typer.echo(f"   {status}: {count} videos")
        
        typer.echo(f"   Total tips extracted: {total_tips}")
        
        # Show recent exports
        exporter = TipsExporter(db_manager, config)
        exports = exporter.get_export_history()
        
        if exports:
            typer.echo("\n📁 Recent exports:")
            for export_file in exports[:5]:
                typer.echo(f"   - {export_file}")
        
    except Exception as e:
        typer.echo(f"❌ Failed to get status: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def export(
    filename: Optional[str] = typer.Option(None, "--filename", help="Custom filename"),
    stats: bool = typer.Option(False, "--stats", help="Export summary statistics")
):
    """Export tips to CSV."""
    initialize_components()
    
    try:
        exporter = TipsExporter(db_manager, config)
        
        if stats:
            typer.echo("📊 Exporting summary statistics...")
            if exporter.export_summary_stats():
                typer.echo("✅ Statistics exported successfully")
            else:
                typer.echo("❌ Statistics export failed")
        else:
            typer.echo("📊 Exporting tips to CSV...")
            if exporter.export_tips(filename):
                typer.echo("✅ Tips exported successfully")
            else:
                typer.echo("❌ Tips export failed")
        
    except Exception as e:
        typer.echo(f"❌ Export failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def cache_stats():
    """Show audio cache statistics."""
    initialize_components()

    try:
        cache_manager = AudioCacheManager(config)
        stats = cache_manager.get_cache_stats()

        typer.echo("🎵 Audio Cache Statistics")
        typer.echo("=" * 30)
        typer.echo(f"   Total files: {stats['total_files']}")
        typer.echo(f"   Total size: {stats['total_size_mb']} MB ({stats['total_size_gb']} GB)")
        typer.echo(f"   Max size: {stats['max_size_gb']} GB")
        typer.echo(f"   Cache directory: {stats['cache_dir']}")

        if stats['status_counts']:
            typer.echo("\n📊 Transcription status:")
            for status, count in stats['status_counts'].items():
                typer.echo(f"   - {status}: {count} files")

    except Exception as e:
        typer.echo(f"❌ Failed to get cache stats: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def cache_cleanup(
    force: bool = typer.Option(False, "--force", help="Force cleanup regardless of time since last cleanup")
):
    """Clean up old audio cache files."""
    initialize_components()

    try:
        cache_manager = AudioCacheManager(config)

        typer.echo("🧹 Cleaning up audio cache...")
        results = cache_manager.cleanup_cache(force=force)

        if results.get('skipped'):
            typer.echo(f"⏭️ Cleanup skipped: {results['reason']}")
        else:
            typer.echo(f"✅ Cleanup completed:")
            typer.echo(f"   - Files removed: {results['files_removed']}")
            typer.echo(f"   - Space freed: {results['space_freed_mb']:.2f} MB")

            if results['errors']:
                typer.echo(f"⚠️ Errors encountered: {len(results['errors'])}")
                for error in results['errors'][:5]:  # Show first 5 errors
                    typer.echo(f"   - {error}")

    except Exception as e:
        typer.echo(f"❌ Cache cleanup failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def cache_clear(
    confirm: bool = typer.Option(False, "--confirm", help="Confirm cache clearing")
):
    """Clear all audio cache files."""
    initialize_components()

    if not confirm:
        typer.echo("⚠️ This will delete all cached audio files.")
        typer.echo("Use --confirm to proceed.")
        raise typer.Exit(1)

    try:
        cache_manager = AudioCacheManager(config)
        stats = cache_manager.get_cache_stats()

        typer.echo(f"🗑️ Clearing {stats['total_files']} cached audio files...")

        # Force cleanup with 0 days (removes everything)
        old_cleanup_days = cache_manager.cleanup_after_days
        cache_manager.cleanup_after_days = 0
        cache_manager.keep_successful_transcripts = False

        results = cache_manager.cleanup_cache(force=True)

        # Restore original settings
        cache_manager.cleanup_after_days = old_cleanup_days
        cache_manager.keep_successful_transcripts = True

        typer.echo(f"✅ Cache cleared:")
        typer.echo(f"   - Files removed: {results['files_removed']}")
        typer.echo(f"   - Space freed: {results['space_freed_mb']:.2f} MB")

    except Exception as e:
        typer.echo(f"❌ Cache clear failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def transcript_cache_stats():
    """Show transcript cache statistics."""
    initialize_components()

    try:
        from .transcript_cache import TranscriptCacheManager

        transcript_cache = TranscriptCacheManager(config)
        stats = transcript_cache.get_cache_stats()

        typer.echo("📊 Transcript Cache Statistics:")
        typer.echo(f"  Total files: {stats['total_files']}")
        typer.echo(f"  Total size: {stats['total_size_mb']} MB")
        typer.echo(f"  Cache directory: {stats['cache_dir']}")
        typer.echo(f"  Created: {stats['created_at']}")
        typer.echo(f"  Last cleanup: {stats['last_cleanup'] or 'Never'}")

    except Exception as e:
        typer.echo(f"❌ Failed to get transcript cache stats: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def transcript_cache_cleanup():
    """Clean up old transcript cache files."""
    initialize_components()

    try:
        from .transcript_cache import TranscriptCacheManager

        transcript_cache = TranscriptCacheManager(config)
        cleaned_count = transcript_cache.cleanup_old_transcripts()

        if cleaned_count > 0:
            typer.echo(f"✅ Cleaned up {cleaned_count} old transcript cache files")
        else:
            typer.echo("✅ No old transcript cache files to clean up")

    except Exception as e:
        typer.echo(f"❌ Transcript cache cleanup failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def transcript_cache_clear(
    confirm: bool = typer.Option(False, "--confirm", help="Confirm cache clearing")
):
    """Clear all transcript cache files."""
    initialize_components()

    try:
        from .transcript_cache import TranscriptCacheManager

        transcript_cache = TranscriptCacheManager(config)
        stats = transcript_cache.get_cache_stats()

        typer.echo(f"⚠️  This will delete {stats['total_files']} transcript cache files ({stats['total_size_mb']} MB)")

        if not confirm:
            typer.echo("Use --confirm to proceed with clearing the transcript cache")
            return

        if transcript_cache.clear_cache():
            typer.echo("✅ Transcript cache cleared successfully")
        else:
            typer.echo("❌ Failed to clear transcript cache")
            raise typer.Exit(1)

    except Exception as e:
        typer.echo(f"❌ Transcript cache clear failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def migrate_transcript_cache():
    """Migrate existing raw transcript files to the new transcript cache."""
    initialize_components()

    try:
        from .migrate_transcript_cache import run_migration

        typer.echo("🔄 Starting transcript cache migration...")
        run_migration(config)

    except Exception as e:
        typer.echo(f"❌ Migration failed: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def reset_errors(
    status: str = typer.Option("transcript_error", help="Status to reset (transcript_error, parse_error, vision_error)"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm the reset operation")
):
    """Reset videos with error status back to 'new' for reprocessing."""
    initialize_components()

    try:
        # Get videos with the specified error status
        error_videos = db_manager.get_videos_by_status(status)

        if not error_videos:
            typer.echo(f"No videos found with status '{status}'")
            return

        typer.echo(f"Found {len(error_videos)} videos with status '{status}':")
        for video in error_videos[:5]:  # Show first 5
            typer.echo(f"  - {video['id']} | {video['published_at']} | {video['title'][:50]}...")

        if len(error_videos) > 5:
            typer.echo(f"  ... and {len(error_videos) - 5} more")

        if not confirm:
            typer.echo("\nTo reset these videos to 'new' status for reprocessing, run:")
            typer.echo(f"python -m src.cli reset-errors --status {status} --confirm")
            return

        # Reset videos to 'new' status
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE videos
                SET status = 'new', last_error = NULL
                WHERE status = ?
            """, (status,))
            conn.commit()

        typer.echo(f"✅ Reset {len(error_videos)} videos from '{status}' to 'new' status")
        typer.echo("These videos will be reprocessed in the next pipeline run.")

    except Exception as e:
        typer.echo(f"❌ Reset failed: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
