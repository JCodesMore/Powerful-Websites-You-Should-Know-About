"""
YouTube API client for video discovery and transcript extraction.

Provides structured interfaces for yt-dlp and youtube-transcript-api with
proper error handling and data validation.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
except ImportError:
    YouTubeTranscriptApi = None
    TextFormatter = None

from .base_client import BaseAPIClient, api_call
from ..exceptions import YouTubeError

logger = logging.getLogger(__name__)


class YouTubeClient(BaseAPIClient):
    """Client for YouTube video operations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize YouTube client.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__('YouTube', config)
        self.channel_url = config.get('youtube', {}).get('channel_url')
        self.since_date = config.get('youtube', {}).get('since_date')
        self.max_videos = config.get('youtube', {}).get('max_videos', 0)
    
    def is_configured(self) -> bool:
        """Check if YouTube client is properly configured."""
        return bool(yt_dlp and self.channel_url)
    
    def test_connection(self) -> bool:
        """Test YouTube API connection."""
        if not self.is_configured():
            return False
        
        try:
            # Test with a simple video info extraction
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                # Try to extract info from a known video
                test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Rick Roll
                info = ydl.extract_info(test_url, download=False)
                return bool(info)
        except Exception as e:
            logger.error(f"YouTube connection test failed: {e}")
            return False
    
    @api_call
    def discover_channel_videos(self) -> List[Dict[str, Any]]:
        """Discover videos from the configured channel.
        
        Returns:
            List of video metadata dictionaries
            
        Raises:
            YouTubeError: If video discovery fails
        """
        if not self.is_configured():
            raise YouTubeError("YouTube client not configured")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'playlistend': self.max_videos if self.max_videos > 0 else None,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                playlist_info = ydl.extract_info(
                    f"{self.channel_url}/shorts",
                    download=False
                )
                
                if not playlist_info or 'entries' not in playlist_info:
                    logger.warning("No videos found in channel")
                    return []
                
                videos = []
                for entry in playlist_info['entries']:
                    if entry and entry.get('id'):
                        video_data = self._extract_video_details(ydl, entry)
                        if video_data:
                            videos.append(video_data)
                
                return videos
                
        except Exception as e:
            raise YouTubeError(f"Failed to discover videos: {str(e)}")
    
    @api_call
    def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a specific video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Video information dictionary or None
            
        Raises:
            YouTubeError: If video info extraction fails
        """
        if not self.is_configured():
            raise YouTubeError("YouTube client not configured")
        
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}",
                    download=False
                )
                return self._normalize_video_info(info)
                
        except Exception as e:
            raise YouTubeError(f"Failed to get video info for {video_id}: {str(e)}")
    
    @api_call
    def get_transcript(self, video_id: str) -> Optional[str]:
        """Get transcript for a video using YouTube's built-in captions.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Transcript text or None if not available
        """
        if not YouTubeTranscriptApi:
            logger.warning("youtube-transcript-api not available")
            return None
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # Try to get English transcript first
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                # If no English, get the first available generated transcript
                transcript = transcript_list.find_generated_transcript(['en'])
            
            # Fetch and format transcript
            transcript_data = transcript.fetch()
            formatter = TextFormatter()
            transcript_text = formatter.format_transcript(transcript_data)
            
            logger.debug(f"Got YouTube transcript for {video_id}")
            return transcript_text.strip()
            
        except Exception as e:
            logger.debug(f"YouTube transcript not available for {video_id}: {e}")
            return None
    
    @api_call
    def get_audio_url(self, video_id: str) -> Optional[str]:
        """Get audio stream URL for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Audio stream URL or None
            
        Raises:
            YouTubeError: If audio URL extraction fails
        """
        if not self.is_configured():
            raise YouTubeError("YouTube client not configured")
        
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}",
                    download=False
                )
                
                # Get the best audio format URL
                if 'url' in info:
                    return info['url']
                elif 'formats' in info:
                    for fmt in info['formats']:
                        if fmt.get('acodec') != 'none' and fmt.get('url'):
                            return fmt['url']
                
                return None
                
        except Exception as e:
            raise YouTubeError(f"Failed to get audio URL for {video_id}: {str(e)}")
    
    @api_call
    def download_video(self, video_id: str, output_path: Path) -> Optional[Path]:
        """Download video file for frame extraction.
        
        Args:
            video_id: YouTube video ID
            output_path: Path where video should be saved
            
        Returns:
            Path to downloaded video file or None
            
        Raises:
            YouTubeError: If video download fails
        """
        if not self.is_configured():
            raise YouTubeError("YouTube client not configured")
        
        try:
            ydl_opts = {
                'format': 'best[height<=720]',  # Limit quality for faster processing
                'outtmpl': str(output_path),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={video_id}"])
            
            if output_path.exists():
                logger.debug(f"Downloaded video: {output_path}")
                return output_path
            else:
                logger.error(f"Video download failed: {output_path}")
                return None
                
        except Exception as e:
            raise YouTubeError(f"Failed to download video {video_id}: {str(e)}")

    @api_call
    def download_audio(self, video_id: str, output_path: Path) -> Optional[Path]:
        """Download audio file for transcription.

        Args:
            video_id: YouTube video ID
            output_path: Path where audio should be saved

        Returns:
            Path to downloaded audio file or None

        Raises:
            YouTubeError: If audio download fails
        """
        if not self.is_configured():
            raise YouTubeError("YouTube client not configured")

        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            ydl_opts = self._get_audio_download_options(output_path)
            self._download_with_ytdlp(video_id, ydl_opts)

            return self._find_downloaded_audio_file(output_path)

        except Exception as e:
            raise YouTubeError(f"Failed to download audio for {video_id}: {str(e)}")

    def _get_audio_download_options(self, output_path: Path) -> Dict[str, Any]:
        """Get yt-dlp options for audio download.

        Args:
            output_path: Path where audio should be saved

        Returns:
            yt-dlp options dictionary
        """
        return {
            'format': 'bestaudio/best',
            'outtmpl': str(output_path.with_suffix('.%(ext)s')),
            'quiet': True,
            'no_warnings': True,
            'extractaudio': True,
            'audioformat': 'wav',  # Convert to WAV for better compatibility
            'audioquality': 0,  # Best quality
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }

    def _download_with_ytdlp(self, video_id: str, ydl_opts: Dict[str, Any]) -> None:
        """Download audio using yt-dlp.

        Args:
            video_id: YouTube video ID
            ydl_opts: yt-dlp options
        """
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f"https://www.youtube.com/watch?v={video_id}"])

    def _find_downloaded_audio_file(self, output_path: Path) -> Optional[Path]:
        """Find the downloaded audio file with possible extension variations.

        Args:
            output_path: Expected output path

        Returns:
            Path to downloaded file or None if not found
        """
        # Check expected path first
        expected_path = output_path.with_suffix('.wav')
        if expected_path.exists():
            logger.debug(f"Downloaded audio: {expected_path}")
            return expected_path

        # Check for other possible extensions
        for ext in ['.wav', '.mp3', '.m4a', '.webm']:
            alt_path = output_path.with_suffix(ext)
            if alt_path.exists():
                return self._handle_alternative_extension(alt_path, ext, output_path)

        logger.error(f"Audio download completed but file not found: {output_path}")
        return None

    def _handle_alternative_extension(self, alt_path: Path, ext: str, output_path: Path) -> Path:
        """Handle downloaded file with alternative extension.

        Args:
            alt_path: Path to file with alternative extension
            ext: File extension
            output_path: Expected output path

        Returns:
            Path to final audio file
        """
        if ext != '.wav':
            final_path = output_path.with_suffix('.wav')
            alt_path.rename(final_path)
            logger.debug(f"Downloaded and renamed audio: {final_path}")
            return final_path
        else:
            logger.debug(f"Downloaded audio: {alt_path}")
            return alt_path

    @api_call
    def get_audio_metadata(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get audio metadata for a video.

        Args:
            video_id: YouTube video ID

        Returns:
            Audio metadata dictionary or None

        Raises:
            YouTubeError: If metadata extraction fails
        """
        if not self.is_configured():
            raise YouTubeError("YouTube client not configured")

        try:
            import time

            with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                info = ydl.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}",
                    download=False
                )

                # Extract relevant audio metadata
                metadata = {
                    'video_id': video_id,
                    'title': info.get('title', ''),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', ''),
                    'upload_date': info.get('upload_date', ''),
                    'extracted_at': time.time(),
                    'audio_formats': []
                }

                # Get available audio formats
                if 'formats' in info:
                    for fmt in info['formats']:
                        if fmt.get('acodec') != 'none':
                            metadata['audio_formats'].append({
                                'format_id': fmt.get('format_id'),
                                'ext': fmt.get('ext'),
                                'acodec': fmt.get('acodec'),
                                'abr': fmt.get('abr'),
                                'filesize': fmt.get('filesize')
                            })

                return metadata

        except Exception as e:
            raise YouTubeError(f"Failed to get audio metadata for {video_id}: {str(e)}")

    def _extract_video_details(self, ydl, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract detailed video information.
        
        Args:
            ydl: YoutubeDL instance
            entry: Basic video entry from playlist
            
        Returns:
            Detailed video information or None
        """
        try:
            video_id = entry.get('id')
            if not video_id:
                return None
            
            # Get detailed video info
            video_info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={video_id}",
                download=False
            )
            
            return self._normalize_video_info(video_info)
            
        except Exception as e:
            logger.error(f"Failed to extract video details: {e}")
            return None
    
    def _normalize_video_info(self, info: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize video information to consistent format.
        
        Args:
            info: Raw video info from yt-dlp
            
        Returns:
            Normalized video information
        """
        video_id = info.get('id', '')
        title = info.get('title', 'Unknown Title')
        duration = info.get('duration', 0)
        
        # Format upload date
        upload_date = info.get('upload_date')
        if upload_date:
            # Convert YYYYMMDD to YYYY-MM-DD
            formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
        else:
            from datetime import datetime
            formatted_date = datetime.now().strftime('%Y-%m-%d')
        
        return {
            'id': video_id,
            'title': title,
            'published_at': formatted_date,
            'duration': duration,
            'url': f"https://www.youtube.com/watch?v={video_id}",
            'raw_info': info  # Keep raw info for debugging
        }
