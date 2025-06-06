"""
AssemblyAI API client for audio transcription.

Provides structured interface for audio transcription with proper error handling
and status polling.
"""

import time
import logging
from typing import Dict, Any, Optional

try:
    import assemblyai as aai
except ImportError:
    aai = None

from .base_client import BaseAPIClient, api_call
from ..exceptions import AssemblyAIError

logger = logging.getLogger(__name__)


class AssemblyAIClient(BaseAPIClient):
    """Client for AssemblyAI transcription API."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize AssemblyAI client.
        
        Args:
            config: Configuration dictionary
        """
        super().__init__('AssemblyAI', config)
        self.api_key = config.get('api_keys', {}).get('assemblyai_api_key')
        
        if self.api_key and aai:
            aai.settings.api_key = self.api_key
            self.transcriber = aai.Transcriber()
        else:
            self.transcriber = None
    
    def is_configured(self) -> bool:
        """Check if AssemblyAI client is properly configured."""
        return bool(self.api_key and aai and self.transcriber)
    
    def test_connection(self) -> bool:
        """Test AssemblyAI API connection."""
        if not self.is_configured():
            return False
        
        try:
            # Test with a simple API call (get account info or similar)
            # Note: AssemblyAI doesn't have a simple ping endpoint,
            # so we'll just check if we can create a transcriber
            return self.transcriber is not None
        except Exception as e:
            logger.error(f"AssemblyAI connection test failed: {e}")
            return False
    
    @api_call
    def transcribe_audio(self, audio_url: str) -> Optional[str]:
        """Transcribe audio from URL.
        
        Args:
            audio_url: URL to audio file
            
        Returns:
            Transcribed text or None if failed
            
        Raises:
            AssemblyAIError: If transcription fails
        """
        if not self.is_configured():
            raise AssemblyAIError("AssemblyAI client not configured")
        
        try:
            # Configure transcription
            config = aai.TranscriptionConfig(
                speech_model=aai.SpeechModel.best,
                language_code="en"
            )
            
            # Submit for transcription
            transcript = self.transcriber.transcribe(audio_url, config=config)
            
            # Poll for completion
            return self._wait_for_completion(transcript)
            
        except Exception as e:
            raise AssemblyAIError(f"Transcription failed: {str(e)}")

    @api_call
    def transcribe_local_audio(self, audio_file_path: str) -> Optional[str]:
        """Transcribe audio from local file.

        Args:
            audio_file_path: Path to local audio file

        Returns:
            Transcribed text or None if failed

        Raises:
            AssemblyAIError: If transcription fails
        """
        if not self.is_configured():
            raise AssemblyAIError("AssemblyAI client not configured")

        try:
            from pathlib import Path

            # Validate file exists
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise AssemblyAIError(f"Audio file not found: {audio_file_path}")

            # Configure transcription
            config = aai.TranscriptionConfig(
                speech_model=aai.SpeechModel.best,
                language_code="en"
            )

            # Submit for transcription using file upload
            with open(audio_path, 'rb') as audio_file:
                transcript = self.transcriber.transcribe(audio_file, config=config)

            # Poll for completion
            return self._wait_for_completion(transcript)

        except Exception as e:
            raise AssemblyAIError(f"Local file transcription failed: {str(e)}")

    @api_call
    def transcribe_local_audio_with_timing(self, audio_file_path: str) -> Optional[Dict[str, Any]]:
        """Transcribe audio from local file and return full timing data.

        Args:
            audio_file_path: Path to local audio file

        Returns:
            Dictionary with text and word-level timing data, or None if failed

        Raises:
            AssemblyAIError: If transcription fails
        """
        if not self.is_configured():
            raise AssemblyAIError("AssemblyAI client not configured")

        try:
            from pathlib import Path

            # Validate file exists
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise AssemblyAIError(f"Audio file not found: {audio_file_path}")

            # Configure transcription
            config = aai.TranscriptionConfig(
                speech_model=aai.SpeechModel.best,
                language_code="en"
            )

            # Submit for transcription using file upload
            with open(audio_path, 'rb') as audio_file:
                transcript = self.transcriber.transcribe(audio_file, config=config)

            # Poll for completion and return full data
            return self._wait_for_completion_with_timing(transcript)

        except Exception as e:
            raise AssemblyAIError(f"Local file transcription with timing failed: {str(e)}")

    @api_call
    def upload_audio_file(self, audio_file_path: str) -> Optional[str]:
        """Upload audio file to AssemblyAI and get URL.

        Args:
            audio_file_path: Path to local audio file

        Returns:
            Uploaded file URL or None if failed

        Raises:
            AssemblyAIError: If upload fails
        """
        if not self.is_configured():
            raise AssemblyAIError("AssemblyAI client not configured")

        try:
            from pathlib import Path

            # Validate file exists
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise AssemblyAIError(f"Audio file not found: {audio_file_path}")

            # Upload file
            with open(audio_path, 'rb') as audio_file:
                upload_url = self.transcriber.upload_file(audio_file)

            return upload_url

        except Exception as e:
            raise AssemblyAIError(f"File upload failed: {str(e)}")

    def _wait_for_completion(self, transcript) -> Optional[str]:
        """Wait for transcription to complete.
        
        Args:
            transcript: AssemblyAI transcript object
            
        Returns:
            Transcribed text or None if failed
            
        Raises:
            AssemblyAIError: If transcription fails
        """
        max_wait_time = 300  # 5 minutes max wait
        poll_interval = 5    # Check every 5 seconds
        elapsed_time = 0
        
        while transcript.status == aai.TranscriptStatus.processing:
            if elapsed_time >= max_wait_time:
                raise AssemblyAIError("Transcription timeout - took longer than 5 minutes")
            
            time.sleep(poll_interval)
            elapsed_time += poll_interval
            
            # Refresh transcript status
            try:
                transcript = self.transcriber.get_transcript(transcript.id)
            except Exception as e:
                raise AssemblyAIError(f"Failed to check transcription status: {str(e)}")
        
        if transcript.status == aai.TranscriptStatus.completed:
            logger.debug(f"AssemblyAI transcription completed in {elapsed_time}s")
            return transcript.text
        else:
            error_msg = getattr(transcript, 'error', 'Unknown error')
            raise AssemblyAIError(f"Transcription failed: {error_msg}")

    def _wait_for_completion_with_timing(self, transcript) -> Optional[Dict[str, Any]]:
        """Wait for transcription to complete and return full timing data.

        Args:
            transcript: AssemblyAI transcript object

        Returns:
            Dictionary with text and word-level timing data, or None if failed

        Raises:
            AssemblyAIError: If transcription fails
        """
        max_wait_time = 300  # 5 minutes max wait
        poll_interval = 5    # Check every 5 seconds
        elapsed_time = 0

        while transcript.status == aai.TranscriptStatus.processing:
            if elapsed_time >= max_wait_time:
                raise AssemblyAIError("Transcription timeout - took longer than 5 minutes")

            time.sleep(poll_interval)
            elapsed_time += poll_interval

            # Refresh transcript status
            try:
                transcript = self.transcriber.get_transcript(transcript.id)
            except Exception as e:
                raise AssemblyAIError(f"Failed to check transcription status: {str(e)}")

        if transcript.status == aai.TranscriptStatus.completed:
            logger.debug(f"AssemblyAI transcription with timing completed in {elapsed_time}s")
            return self._extract_transcript_with_timing(transcript)
        else:
            error_msg = getattr(transcript, 'error', 'Unknown error')
            raise AssemblyAIError(f"Transcription failed: {error_msg}")

    def _extract_transcript_with_timing(self, transcript) -> Dict[str, Any]:
        """Extract both text and word-level timing data from AssemblyAI transcript.

        Args:
            transcript: AssemblyAI transcript object

        Returns:
            Dictionary containing text, words with timing, and metadata
        """
        return {
            'text': transcript.text,
            'words': [
                {
                    'text': word.text,
                    'start': word.start,  # milliseconds
                    'end': word.end,      # milliseconds
                    'confidence': word.confidence
                }
                for word in transcript.words
            ] if transcript.words else [],
            'confidence': getattr(transcript, 'confidence', None),
            'audio_duration': getattr(transcript, 'audio_duration', None)
        }

    def get_transcript_metadata(self, transcript_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a completed transcript.
        
        Args:
            transcript_id: AssemblyAI transcript ID
            
        Returns:
            Transcript metadata or None if not found
        """
        if not self.is_configured():
            return None
        
        try:
            transcript = self.transcriber.get_transcript(transcript_id)
            
            return {
                'id': transcript.id,
                'status': transcript.status,
                'text': transcript.text,
                'confidence': getattr(transcript, 'confidence', None),
                'audio_duration': getattr(transcript, 'audio_duration', None),
                'created': getattr(transcript, 'created', None),
                'completed': getattr(transcript, 'completed', None)
            }
            
        except Exception as e:
            logger.error(f"Failed to get transcript metadata: {e}")
            return None
