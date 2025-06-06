"""
Data validation utilities for the scraper.

Provides consistent validation for video data, tips, configuration,
and other data structures.
"""

import re
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from ..exceptions import ValidationError

logger = logging.getLogger(__name__)


class DataValidator:
    """Centralized data validation with consistent error handling."""
    
    # Common regex patterns
    VIDEO_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{11}$')
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    WEBSITE_PATTERN = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    )
    DATE_PATTERN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    
    @classmethod
    def validate_video_id(cls, video_id: str) -> str:
        """Validate YouTube video ID format.
        
        Args:
            video_id: Video ID to validate
            
        Returns:
            Validated video ID
            
        Raises:
            ValidationError: If video ID is invalid
        """
        if not isinstance(video_id, str):
            raise ValidationError("Video ID must be a string", "video_id", video_id)
        
        if not video_id:
            raise ValidationError("Video ID cannot be empty", "video_id", video_id)
        
        if not cls.VIDEO_ID_PATTERN.match(video_id):
            raise ValidationError(
                "Invalid YouTube video ID format", 
                "video_id", 
                video_id
            )
        
        return video_id
    
    @classmethod
    def validate_video_data(cls, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate video data structure.
        
        Args:
            video_data: Video data dictionary
            
        Returns:
            Validated video data
            
        Raises:
            ValidationError: If video data is invalid
        """
        if not isinstance(video_data, dict):
            raise ValidationError("Video data must be a dictionary", "video_data", type(video_data))
        
        required_fields = ['id', 'title', 'published_at']
        for field in required_fields:
            if field not in video_data:
                raise ValidationError(f"Missing required field: {field}", field, None)
        
        # Validate video ID
        video_data['id'] = cls.validate_video_id(video_data['id'])
        
        # Validate title
        if not isinstance(video_data['title'], str) or not video_data['title'].strip():
            raise ValidationError("Video title must be a non-empty string", "title", video_data['title'])
        
        # Validate date
        video_data['published_at'] = cls.validate_date(video_data['published_at'])
        
        # Validate optional duration
        if 'duration' in video_data:
            duration = video_data['duration']
            if not isinstance(duration, (int, float)) or duration < 0:
                raise ValidationError("Duration must be a non-negative number", "duration", duration)
        
        return video_data
    
    @classmethod
    def validate_tip_data(cls, tip_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tip data structure.
        
        Args:
            tip_data: Tip data dictionary
            
        Returns:
            Validated tip data
            
        Raises:
            ValidationError: If tip data is invalid
        """
        if not isinstance(tip_data, dict):
            raise ValidationError("Tip data must be a dictionary", "tip_data", type(tip_data))
        
        required_fields = ['website', 'use', 'details']
        for field in required_fields:
            if field not in tip_data:
                raise ValidationError(f"Missing required field: {field}", field, None)
        
        # Validate website
        website = tip_data['website']
        if not isinstance(website, str) or not website.strip():
            raise ValidationError("Website must be a non-empty string", "website", website)
        
        # Clean and validate website format
        website = website.strip().lower()
        if not cls.WEBSITE_PATTERN.match(website) and not cls.URL_PATTERN.match(f"https://{website}"):
            logger.warning(f"Website format may be invalid: {website}")
        
        tip_data['website'] = website
        
        # Validate use and details
        for field in ['use', 'details']:
            value = tip_data[field]
            if not isinstance(value, str):
                tip_data[field] = str(value)
        
        # Ensure frame_path exists
        if 'frame_path' not in tip_data:
            tip_data['frame_path'] = ''
        
        return tip_data
    
    @classmethod
    def validate_tips_list(cls, tips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate a list of tips.
        
        Args:
            tips: List of tip dictionaries
            
        Returns:
            List of validated tips
            
        Raises:
            ValidationError: If tips list is invalid
        """
        if not isinstance(tips, list):
            raise ValidationError("Tips must be a list", "tips", type(tips))
        
        validated_tips = []
        for i, tip in enumerate(tips):
            try:
                validated_tip = cls.validate_tip_data(tip)
                validated_tips.append(validated_tip)
            except ValidationError as e:
                logger.warning(f"Invalid tip at index {i}: {e}")
                # Skip invalid tips rather than failing completely
                continue
        
        return validated_tips
    
    @classmethod
    def validate_date(cls, date_str: str) -> str:
        """Validate date string format (YYYY-MM-DD).
        
        Args:
            date_str: Date string to validate
            
        Returns:
            Validated date string
            
        Raises:
            ValidationError: If date format is invalid
        """
        if not isinstance(date_str, str):
            raise ValidationError("Date must be a string", "date", date_str)
        
        if not cls.DATE_PATTERN.match(date_str):
            raise ValidationError("Date must be in YYYY-MM-DD format", "date", date_str)
        
        # Try to parse the date to ensure it's valid
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError as e:
            raise ValidationError(f"Invalid date: {e}", "date", date_str)
        
        return date_str
    
    @classmethod
    def validate_config(cls, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration structure.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            Validated configuration
            
        Raises:
            ValidationError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary", "config", type(config))
        
        # Validate required sections
        required_sections = ['youtube', 'api_keys', 'rate_limits']
        for section in required_sections:
            if section not in config:
                raise ValidationError(f"Missing configuration section: {section}", section, None)
        
        # Validate YouTube configuration
        youtube_config = config['youtube']
        if 'channel_url' not in youtube_config:
            raise ValidationError("Missing YouTube channel URL", "channel_url", None)
        
        channel_url = youtube_config['channel_url']
        if not isinstance(channel_url, str) or not channel_url.strip():
            raise ValidationError("Channel URL must be a non-empty string", "channel_url", channel_url)
        
        # Validate API keys section exists (keys themselves are optional)
        api_keys = config['api_keys']
        if not isinstance(api_keys, dict):
            raise ValidationError("API keys must be a dictionary", "api_keys", type(api_keys))
        
        # Validate rate limits
        rate_limits = config['rate_limits']
        if not isinstance(rate_limits, dict):
            raise ValidationError("Rate limits must be a dictionary", "rate_limits", type(rate_limits))
        
        return config
    
    @classmethod
    def validate_transcript(cls, transcript: str) -> str:
        """Validate transcript text.
        
        Args:
            transcript: Transcript text to validate
            
        Returns:
            Validated transcript text
            
        Raises:
            ValidationError: If transcript is invalid
        """
        if not isinstance(transcript, str):
            raise ValidationError("Transcript must be a string", "transcript", type(transcript))
        
        transcript = transcript.strip()
        if not transcript:
            raise ValidationError("Transcript cannot be empty", "transcript", transcript)
        
        # Check for minimum length (transcripts should have some content)
        if len(transcript) < 10:
            raise ValidationError("Transcript too short (minimum 10 characters)", "transcript", len(transcript))
        
        return transcript
    
    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe file system usage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        if not isinstance(filename, str):
            filename = str(filename)
        
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing whitespace and dots
        filename = filename.strip(' .')
        
        # Ensure filename is not empty
        if not filename:
            filename = 'unnamed'
        
        # Limit length
        if len(filename) > 255:
            filename = filename[:255]
        
        return filename
    
    @classmethod
    def validate_file_path(cls, file_path: str) -> str:
        """Validate file path format.
        
        Args:
            file_path: File path to validate
            
        Returns:
            Validated file path
            
        Raises:
            ValidationError: If file path is invalid
        """
        if not isinstance(file_path, str):
            raise ValidationError("File path must be a string", "file_path", type(file_path))
        
        if not file_path.strip():
            raise ValidationError("File path cannot be empty", "file_path", file_path)
        
        # Check for invalid characters (basic check)
        if any(char in file_path for char in ['<', '>', '|', '?', '*']):
            raise ValidationError("File path contains invalid characters", "file_path", file_path)
        
        return file_path.strip()
