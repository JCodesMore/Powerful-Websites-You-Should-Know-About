"""
Database helpers for SetupSpawn Shorts Scraper.

Handles SQLite database operations, schema creation, and data persistence.
"""

import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager

from .utils import PathSerializer

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages SQLite database operations for the scraper."""
    
    def __init__(self, db_path: str):
        """Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema if it doesn't exist."""
        with self.get_connection() as conn:
            # Create videos table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    id TEXT PRIMARY KEY,
                    title TEXT,
                    published_at TEXT,
                    status TEXT DEFAULT 'new',
                    transcript TEXT,
                    transcript_data TEXT,
                    last_error TEXT
                )
            """)

            # Add transcript_data column if it doesn't exist (for existing databases)
            try:
                conn.execute("ALTER TABLE videos ADD COLUMN transcript_data TEXT")
                logger.info("Added transcript_data column to videos table")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Create tips table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tips (
                    video_id TEXT,
                    website TEXT,
                    use TEXT,
                    details TEXT,
                    frame_path TEXT,
                    PRIMARY KEY (video_id, website),
                    FOREIGN KEY (video_id) REFERENCES videos(id)
                )
            """)

            # Add multi-frame columns if they don't exist (for existing databases)
            try:
                conn.execute("ALTER TABLE tips ADD COLUMN frame_paths TEXT")  # JSON array of all frame paths
                logger.info("Added frame_paths column to tips table")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                conn.execute("ALTER TABLE tips ADD COLUMN successful_frame_index INTEGER")  # Which frame succeeded
                logger.info("Added successful_frame_index column to tips table")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                conn.execute("ALTER TABLE tips ADD COLUMN frame_analysis_metadata TEXT")  # JSON metadata
                logger.info("Added frame_analysis_metadata column to tips table")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            # Create indexes for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_status
                ON videos(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tips_video_id
                ON tips(video_id)
            """)

            conn.commit()
            logger.info("Database schema initialized")
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper cleanup."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
        finally:
            conn.close()
    
    def insert_video(self, video_id: str, title: str, published_at: str) -> bool:
        """Insert a new video record.
        
        Args:
            video_id: YouTube video ID
            title: Video title
            published_at: Publication timestamp
            
        Returns:
            True if inserted, False if already exists
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO videos (id, title, published_at)
                    VALUES (?, ?, ?)
                """, (video_id, title, published_at))
                conn.commit()
                return conn.total_changes > 0
        except Exception as e:
            logger.error(f"Failed to insert video {video_id}: {e}")
            return False
    
    def update_video_status(self, video_id: str, status: str, error: str = None) -> bool:
        """Update video processing status.

        Args:
            video_id: YouTube video ID
            status: New status
            error: Error message if status indicates failure

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE videos
                    SET status = ?, last_error = ?
                    WHERE id = ?
                """, (status, error, video_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update video status {video_id}: {e}")
            return False

    def update_video_transcript(self, video_id: str, transcript_text: str) -> bool:
        """Update video record with transcript text.

        Args:
            video_id: YouTube video ID
            transcript_text: Transcript text to save

        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE videos
                    SET transcript = ?
                    WHERE id = ?
                """, (transcript_text, video_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update transcript for {video_id}: {e}")
            return False

    def update_video_transcript_data(self, video_id: str, transcript_data: Dict[str, Any]) -> bool:
        """Update video record with full transcript data including timing.

        Args:
            video_id: YouTube video ID
            transcript_data: Full transcript data with timing information

        Returns:
            True if successful, False otherwise
        """
        try:
            import json

            with self.get_connection() as conn:
                conn.execute("""
                    UPDATE videos
                    SET transcript = ?, transcript_data = ?
                    WHERE id = ?
                """, (transcript_data.get('text', ''), json.dumps(transcript_data), video_id))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to update transcript data for {video_id}: {e}")
            return False
    
    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get a single video by ID.

        Args:
            video_id: YouTube video ID

        Returns:
            Video record or None if not found
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM videos WHERE id = ?
                """, (video_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to get video {video_id}: {e}")
            return None

    def get_videos_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get videos with specific status.

        Args:
            status: Status to filter by

        Returns:
            List of video records
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM videos WHERE status = ?
                    ORDER BY published_at DESC
                """, (status,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get videos by status {status}: {e}")
            return []
    
    def insert_tips(self, video_id: str, tips: List[Dict[str, str]]):
        """Insert tips for a video.

        Args:
            video_id: YouTube video ID
            tips: List of tip dictionaries with website, use, details, frame_path, and optional multi-frame metadata
        """
        try:
            with self.get_connection() as conn:
                for tip in tips:
                    # Prepare multi-frame metadata using PathSerializer
                    frame_paths_json = None
                    if 'frame_paths' in tip and tip['frame_paths']:
                        frame_paths_json = PathSerializer.serialize_path_list(tip['frame_paths'])

                    frame_metadata_json = None
                    if 'frame_analysis_metadata' in tip and tip['frame_analysis_metadata']:
                        frame_metadata_json = PathSerializer.serialize_frame_metadata(tip['frame_analysis_metadata'])

                    conn.execute("""
                        INSERT OR REPLACE INTO tips
                        (video_id, website, use, details, frame_path, frame_paths, successful_frame_index, frame_analysis_metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        video_id,
                        tip.get('website', ''),
                        tip.get('use', ''),
                        tip.get('details', ''),
                        tip.get('frame_path', ''),
                        frame_paths_json,
                        tip.get('successful_frame_index'),
                        frame_metadata_json
                    ))
                conn.commit()
                logger.info(f"Inserted {len(tips)} tips for video {video_id}")
        except Exception as e:
            logger.error(f"Failed to insert tips for video {video_id}: {e}")
    
    def get_all_tips(self) -> List[Dict[str, Any]]:
        """Get all tips with video information, including videos without tips.

        Returns:
            List of tip records joined with video data, includes all videos even without tips
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT
                        v.id as video_id,
                        v.title as video_title,
                        v.published_at,
                        COALESCE(t.website, 'No tips found') as website,
                        COALESCE(t.use, 'Processing failed or no content found') as use,
                        COALESCE(t.details, CASE
                            WHEN v.status LIKE '%_error' THEN 'Error: ' || COALESCE(v.last_error, 'Unknown error')
                            WHEN v.status = 'new' THEN 'Not yet processed'
                            WHEN v.status = 'transcribed' THEN 'Transcript extracted, parsing pending'
                            WHEN v.status = 'parsed' THEN 'Parsed, vision analysis pending'
                            ELSE 'Processing status: ' || v.status
                        END) as details,
                        COALESCE(t.frame_path, '') as frame_path
                    FROM videos v
                    LEFT JOIN tips t ON t.video_id = v.id
                    ORDER BY v.published_at DESC, t.website
                """)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get all tips: {e}")
            return []
