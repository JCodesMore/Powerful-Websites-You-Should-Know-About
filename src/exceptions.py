"""
Custom exception hierarchy for SetupSpawn Shorts Scraper.

Provides structured error handling with clear error context and recovery information.
"""

from typing import Optional, Dict, Any


class ScraperError(Exception):
    """Base exception for all scraper-related errors."""
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        """Initialize scraper error.
        
        Args:
            message: Human-readable error message
            context: Additional context information for debugging
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}
    
    def __str__(self) -> str:
        """Return formatted error message with context."""
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            return f"{self.message} (Context: {context_str})"
        return self.message


class ConfigurationError(ScraperError):
    """Raised when configuration is invalid or missing."""
    pass


class DatabaseError(ScraperError):
    """Raised when database operations fail."""
    pass


class VideoDiscoveryError(ScraperError):
    """Raised when video discovery fails."""
    pass


class TranscriptError(ScraperError):
    """Raised when transcript extraction fails."""
    pass


class ParseError(ScraperError):
    """Raised when text parsing fails."""
    pass


class VisionError(ScraperError):
    """Raised when vision analysis fails."""
    pass


class ExportError(ScraperError):
    """Raised when data export fails."""
    pass


class APIError(ScraperError):
    """Base class for API-related errors."""
    
    def __init__(self, message: str, api_name: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        """Initialize API error.
        
        Args:
            message: Error message
            api_name: Name of the API that failed
            status_code: HTTP status code if applicable
            response_data: API response data if available
        """
        context = {'api_name': api_name}
        if status_code:
            context['status_code'] = status_code
        if response_data:
            context['response_data'] = response_data
        
        super().__init__(message, context)
        self.api_name = api_name
        self.status_code = status_code
        self.response_data = response_data


class OpenAIError(APIError):
    """Raised when OpenAI API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, 'OpenAI', status_code, response_data)


class AssemblyAIError(APIError):
    """Raised when AssemblyAI API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, 'AssemblyAI', status_code, response_data)


class YouTubeError(APIError):
    """Raised when YouTube API calls fail."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message, 'YouTube', status_code, response_data)


class RateLimitError(APIError):
    """Raised when API rate limits are exceeded."""
    
    def __init__(self, api_name: str, retry_after: Optional[int] = None):
        """Initialize rate limit error.
        
        Args:
            api_name: Name of the API that hit rate limit
            retry_after: Seconds to wait before retrying
        """
        message = f"Rate limit exceeded for {api_name}"
        if retry_after:
            message += f", retry after {retry_after} seconds"
        
        context = {'retry_after': retry_after} if retry_after else {}
        super().__init__(message, api_name, 429, context)
        self.retry_after = retry_after


class ValidationError(ScraperError):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None):
        """Initialize validation error.
        
        Args:
            message: Validation error message
            field: Name of the field that failed validation
            value: The invalid value
        """
        context = {}
        if field:
            context['field'] = field
        if value is not None:
            context['value'] = str(value)
        
        super().__init__(message, context)
        self.field = field
        self.value = value


class FileOperationError(ScraperError):
    """Raised when file operations fail."""
    
    def __init__(self, message: str, file_path: Optional[str] = None, 
                 operation: Optional[str] = None):
        """Initialize file operation error.
        
        Args:
            message: Error message
            file_path: Path to the file that caused the error
            operation: Type of operation that failed (read, write, delete, etc.)
        """
        context = {}
        if file_path:
            context['file_path'] = file_path
        if operation:
            context['operation'] = operation
        
        super().__init__(message, context)
        self.file_path = file_path
        self.operation = operation


class RetryableError(ScraperError):
    """Base class for errors that can be retried."""
    
    def __init__(self, message: str, max_retries: int = 3, 
                 context: Optional[Dict[str, Any]] = None):
        """Initialize retryable error.
        
        Args:
            message: Error message
            max_retries: Maximum number of retry attempts
            context: Additional context information
        """
        super().__init__(message, context)
        self.max_retries = max_retries


class NonRetryableError(ScraperError):
    """Base class for errors that should not be retried."""
    pass


class AudioCacheError(ScraperError):
    """Raised when audio cache operations fail."""
    pass


class AudioDownloadError(AudioCacheError):
    """Raised when audio download fails."""

    def __init__(self, message: str, video_id: Optional[str] = None,
                 download_url: Optional[str] = None):
        """Initialize audio download error.

        Args:
            message: Error message
            video_id: YouTube video ID that failed to download
            download_url: URL that failed to download
        """
        context = {}
        if video_id:
            context['video_id'] = video_id
        if download_url:
            context['download_url'] = download_url

        super().__init__(message, context)
        self.video_id = video_id
        self.download_url = download_url


class CacheCorruptionError(AudioCacheError):
    """Raised when cache index is corrupted or inconsistent."""

    def __init__(self, message: str, cache_file: Optional[str] = None):
        """Initialize cache corruption error.

        Args:
            message: Error message
            cache_file: Path to corrupted cache file
        """
        context = {'cache_file': cache_file} if cache_file else {}
        super().__init__(message, context)
        self.cache_file = cache_file


class StorageLimitError(AudioCacheError):
    """Raised when cache storage limit is exceeded."""

    def __init__(self, message: str, current_size: Optional[float] = None,
                 max_size: Optional[float] = None):
        """Initialize storage limit error.

        Args:
            message: Error message
            current_size: Current cache size in GB
            max_size: Maximum allowed cache size in GB
        """
        context = {}
        if current_size is not None:
            context['current_size_gb'] = current_size
        if max_size is not None:
            context['max_size_gb'] = max_size

        super().__init__(message, context)
        self.current_size = current_size
        self.max_size = max_size


class CacheIndexError(AudioCacheError):
    """Raised when cache index operations fail."""

    def __init__(self, message: str, operation: Optional[str] = None):
        """Initialize cache index error.

        Args:
            message: Error message
            operation: Operation that failed (load, save, update)
        """
        context = {'operation': operation} if operation else {}
        super().__init__(message, context)
        self.operation = operation
