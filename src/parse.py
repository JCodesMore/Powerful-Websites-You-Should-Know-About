"""
Phase 3: Text Parsing with gpt-4.1-mini

Parses transcripts to extract website tips using OpenAI's gpt-4.1-mini model.
"""

import logging
from typing import Dict, Any, List, Optional

from .db import DatabaseManager
from .clients import OpenAIClient
from .utils import DataValidator
from .utils.logging_helper import LoggingMixin
from .exceptions import ParseError, ValidationError

logger = logging.getLogger(__name__)


class TextParser(LoggingMixin):
    """Parses transcripts to extract website tips using gpt-4.1-mini."""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """Initialize text parser.

        Args:
            db_manager: Database manager instance
            config: Configuration dictionary
        """
        super().__init__()
        self.db_manager = db_manager
        self.config = config

        # Initialize clients and utilities
        self.openai_client = OpenAIClient(config)
        self.validator = DataValidator()

        # Set logging context
        self.set_logging_context({
            'component': 'TextParser'
        })
    
    def parse_transcript(self, video_id: str) -> bool:
        """Parse transcript to extract website tips.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate video ID
            self.validator.validate_video_id(video_id)
            self.log_info(f"Parsing transcript for video: {video_id}")

            # Get and validate transcript
            transcript = self._get_video_transcript(video_id)
            if not transcript:
                return self._handle_parse_failure(video_id, "No transcript available")

            # Extract tips using gpt-4.1-mini
            tips = self._extract_tips_from_transcript(transcript)

            # Save results
            return self._save_parsing_results(video_id, tips)

        except ValidationError as e:
            return self._handle_parse_failure(video_id, f"Invalid video ID: {e}")
        except Exception as e:
            return self._handle_parse_failure(video_id, f"Parsing failed: {str(e)}")
    
    def _get_video_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript for a video from database.

        Args:
            video_id: YouTube video ID

        Returns:
            Transcript text or None if not available
        """
        try:
            video = self.db_manager.get_video(video_id)
            if not video or not video.get('transcript'):
                return None

            transcript = video['transcript']
            return self.validator.validate_transcript(transcript)

        except ValidationError as e:
            self.log_error(f"Invalid transcript for {video_id}: {e}")
            return None
        except Exception as e:
            self.log_error(f"Failed to get transcript for {video_id}: {e}")
            return None
    
    def _extract_tips_from_transcript(self, transcript: str) -> List[Dict[str, str]]:
        """Extract website tips from transcript using gpt-4.1-mini.

        Args:
            transcript: Video transcript text

        Returns:
            List of extracted and validated tips
        """
        if not self.openai_client.is_configured():
            self.log_warning("OpenAI client not configured")
            return []

        try:
            # Use OpenAI client to extract tips
            tips = self.openai_client.extract_website_tips(transcript)

            # Validate tips
            validated_tips = self.validator.validate_tips_list(tips)

            self.log_debug(f"Extracted {len(validated_tips)} tips from transcript")
            return validated_tips

        except Exception as e:
            self.log_error(f"Failed to extract tips with GPT: {e}")
            return []

    def _save_parsing_results(self, video_id: str, tips: List[Dict[str, str]]) -> bool:
        """Save parsing results to database.

        Args:
            video_id: YouTube video ID
            tips: List of extracted tips

        Returns:
            True if successful
        """
        try:
            # Save tips to database (use insert_tips which takes a list)
            if tips:
                self.db_manager.insert_tips(video_id, tips)

            # Update video status
            self.db_manager.update_video_status(video_id, 'parsed')

            if tips:
                self.log_info(f"Successfully parsed {len(tips)} tips from {video_id}")
            else:
                self.log_info(f"No tips found in {video_id}, but parsing completed")

            return True

        except Exception as e:
            return self._handle_parse_failure(video_id, f"Failed to save results: {e}")

    def _handle_parse_failure(self, video_id: str, error_msg: str) -> bool:
        """Handle parsing failure.

        Args:
            video_id: YouTube video ID
            error_msg: Error message

        Returns:
            False
        """
        self.log_error(f"Cannot parse {video_id}: {error_msg}")
        self.db_manager.update_video_status(video_id, 'parse_error', error_msg)
        return False
    
    def get_parsed_videos(self) -> List[Dict[str, Any]]:
        """Get videos that have been parsed.
        
        Returns:
            List of videos with 'parsed' status
        """
        return self.db_manager.get_videos_by_status('parsed')
    
    def reparse_video(self, video_id: str) -> bool:
        """Re-parse a video's transcript.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Re-parsing video: {video_id}")
        
        # Reset status to allow re-parsing
        self.db_manager.update_video_status(video_id, 'transcribed')
        
        # Clear existing tips
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("DELETE FROM tips WHERE video_id = ?", (video_id,))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to clear existing tips for {video_id}: {e}")
        
        # Parse again
        return self.parse_transcript(video_id)
