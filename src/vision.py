"""
Phase 4: Vision Analysis with gpt-4.1-mini

Extracts frames around website mentions and uses gpt-4.1-mini vision to detect URLs.
"""

import logging
import base64
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from .db import DatabaseManager
from .clients import OpenAIClient, YouTubeClient
from .utils import FileManager, DataValidator, MetadataManager
from .utils.logging_helper import LoggingMixin
from .exceptions import ValidationError

logger = logging.getLogger(__name__)


class VisionAnalyzer(LoggingMixin):
    """Analyzes video frames to detect URLs using gpt-4.1-mini vision."""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """Initialize vision analyzer.

        Args:
            db_manager: Database manager instance
            config: Configuration dictionary
        """
        super().__init__()
        self.db_manager = db_manager
        self.config = config

        # Initialize clients and utilities
        self.openai_client = OpenAIClient(config)
        self.youtube_client = YouTubeClient(config)
        self.file_manager = FileManager()
        self.validator = DataValidator()

        # Frame extraction settings
        self.context_window = config['processing']['frame_extraction'].get('context_window', 2.0)
        self.max_frames = config['processing']['frame_extraction'].get('max_frames_per_video', 1)
        self.jpeg_quality = config['processing']['frame_extraction'].get('jpeg_quality', 85)
        self.retain_frames = config['processing']['frame_extraction'].get('retain_frames', True)
        self.use_transcript_timing = config['processing']['frame_extraction'].get('use_transcript_timing', True)

        # Multi-frame extraction settings
        multi_frame_config = config['processing']['frame_extraction'].get('multi_frame_extraction', {})
        self.multi_frame_enabled = multi_frame_config.get('enabled', False)
        self.frame_count = multi_frame_config.get('frame_count', 3)
        self.frame_intervals = multi_frame_config.get('frame_intervals', [0, 1.0, 2.0])
        self.early_termination = multi_frame_config.get('early_termination', True)
        self.confidence_threshold = multi_frame_config.get('confidence_threshold', 80)

        # Override max_frames when multi-frame extraction is enabled
        if self.multi_frame_enabled:
            self.max_frames = self.frame_count

        # Set logging context
        self.set_logging_context({
            'component': 'VisionAnalyzer'
        })
    
    def analyze_video(self, video_id: str) -> bool:
        """Analyze video frames for URL detection.

        Args:
            video_id: YouTube video ID

        Returns:
            True if successful, False otherwise

        Raises:
            VisionError: If vision analysis fails
        """
        try:
            # Validate video ID
            self.validator.validate_video_id(video_id)
            self.log_info(f"Starting vision analysis for video: {video_id}")

            # Check if OpenAI client is configured
            if not self.openai_client.is_configured():
                return self._handle_vision_failure(video_id, "OpenAI client not configured")

            # Get existing tips that need analysis
            tips = self._get_video_tips(video_id)

            # If no tips found, check for trigger phrases in transcript
            if not tips:
                tips = self._detect_trigger_phrases(video_id)

            if not tips:
                return self._handle_no_tips(video_id)

            # Download and analyze video
            return self._process_video_analysis(video_id, tips)

        except ValidationError as e:
            return self._handle_vision_failure(video_id, f"Invalid video ID: {e}")
        except Exception as e:
            return self._handle_vision_failure(video_id, f"Vision analysis failed: {str(e)}")

    def _get_video_tips(self, video_id: str) -> List[Dict[str, Any]]:
        """Get tips for a video that need frame analysis.

        Args:
            video_id: YouTube video ID

        Returns:
            List of tip records
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM tips WHERE video_id = ?
                """, (video_id,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.log_error(f"Failed to get tips for {video_id}: {e}")
            return []

    def _detect_trigger_phrases(self, video_id: str) -> List[Dict[str, Any]]:
        """Detect trigger phrases in transcript that suggest website mentions.

        Args:
            video_id: YouTube video ID

        Returns:
            List of placeholder tips for vision analysis
        """
        try:
            # Get video transcript
            video = self.db_manager.get_video(video_id)
            if not video or not video.get('transcript'):
                self.log_debug(f"No transcript available for trigger phrase detection: {video_id}")
                return []

            transcript = video['transcript'].lower()

            # Define trigger phrases that suggest website mentions
            # Only use "this" as specified in requirements
            trigger_phrases = [
                'this'
            ]

            # Check if any trigger phrases are present
            found_triggers = []
            for phrase in trigger_phrases:
                if phrase in transcript:
                    found_triggers.append(phrase)

            if found_triggers:
                self.log_info(f"Found trigger phrases in {video_id}: {found_triggers}")

                # Create placeholder tip for vision analysis
                # Note: This will be replaced with proper website info once discovered
                placeholder_tip = {
                    'video_id': video_id,
                    'website': 'unknown_website',  # Placeholder - will be detected by vision
                    'use': 'pending_extraction',  # Will be filled by GPT analysis after URL discovery
                    'details': 'pending_extraction',  # Will be filled by GPT analysis after URL discovery
                    'frame_path': ''
                }

                return [placeholder_tip]
            else:
                self.log_debug(f"No trigger phrases found in {video_id}")
                return []

        except Exception as e:
            self.log_error(f"Failed to detect trigger phrases for {video_id}: {e}")
            return []

    def _handle_no_tips(self, video_id: str) -> bool:
        """Handle case where video has no tips to analyze.

        Args:
            video_id: YouTube video ID

        Returns:
            True
        """
        self.db_manager.update_video_status(video_id, 'vision_done')
        self.log_info(f"No tips to analyze for {video_id}")
        return True

    def _process_video_analysis(self, video_id: str, tips: List[Dict[str, Any]]) -> bool:
        """Process video analysis for all tips.

        Args:
            video_id: YouTube video ID
            tips: List of tips to analyze

        Returns:
            True if successful
        """
        # Download video for frame extraction
        video_path = self._download_video(video_id)
        if not video_path:
            return self._handle_vision_failure(video_id, "Failed to download video")

        try:
            # Analyze frames for each tip
            success_count = 0
            for tip in tips:
                if self._analyze_tip_frames(video_id, video_path, tip):
                    success_count += 1

            # Update status
            self.db_manager.update_video_status(video_id, 'vision_done')
            self.log_info(f"Vision analysis complete for {video_id}: {success_count}/{len(tips)} tips analyzed")
            return True

        finally:
            # Always clean up video file
            self._cleanup_video(video_path)

    def _handle_vision_failure(self, video_id: str, error_msg: str) -> bool:
        """Handle vision analysis failure.

        Args:
            video_id: YouTube video ID
            error_msg: Error message

        Returns:
            False
        """
        self.log_error(f"Cannot analyze {video_id}: {error_msg}")
        self.db_manager.update_video_status(video_id, 'vision_error', error_msg)
        return False
    
    def _download_video(self, video_id: str) -> Optional[Path]:
        """Download video for frame extraction.

        Args:
            video_id: YouTube video ID

        Returns:
            Path to downloaded video file or None
        """
        try:
            output_path = Path(f"data/raw/video_{video_id}.mp4")
            video_path = self.youtube_client.download_video(video_id, output_path)

            if video_path:
                self.log_debug(f"Downloaded video: {video_path}")
                # Register for cleanup
                self.file_manager.register_temp_file(video_path)
                return video_path
            else:
                self.log_error(f"Video download failed for {video_id}")
                return None

        except Exception as e:
            self.log_error(f"Failed to download video {video_id}: {e}")
            return None
    
    def _analyze_tip_frames(self, video_id: str, video_path: Path, tip: Dict[str, Any]) -> bool:
        """Analyze frames for a specific tip.

        Args:
            video_id: YouTube video ID
            video_path: Path to video file
            tip: Tip record from database

        Returns:
            True if successful, False otherwise
        """
        try:
            website = tip['website']
            self.log_debug(f"Analyzing frames for tip: {website}")

            # Extract frames around potential website mentions
            frame_paths = self._extract_frames(video_path, website)

            if not frame_paths:
                self.log_debug(f"No frames extracted for tip: {website}")
                return True  # Not an error, just no frames to analyze

            # Handle placeholder tips (trigger phrase detection)
            if website == 'unknown_website':
                return self._discover_website_from_frames(video_id, frame_paths, tip)
            else:
                # Analyze frames for known website
                best_frame = self._find_best_frame(frame_paths, website)

                # Update tip with best frame
                if best_frame:
                    self._update_tip_frame(video_id, website, str(best_frame))
                    self.log_debug(f"Updated tip {website} with frame: {best_frame}")

                # Clean up frame files (only if retention is disabled)
                if not self.retain_frames:
                    self._cleanup_frames(frame_paths)
                return True

        except Exception as e:
            website = tip.get('website', 'unknown')
            self.log_error(f"Failed to analyze tip frames for {website}: {e}")
            return False

    def _find_best_frame(self, frame_paths: List[Path], website: str) -> Optional[Path]:
        """Find the best frame for a website using gpt-4.1-mini vision.

        Args:
            frame_paths: List of frame paths to analyze
            website: Website name to look for

        Returns:
            Path to best frame or None
        """
        best_frame = None
        best_confidence = 0

        for frame_path in frame_paths:
            try:
                # Encode frame as base64
                with open(frame_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')

                # Analyze with OpenAI client
                url_info = self.openai_client.analyze_frame_for_urls(image_data, website)

                if url_info and url_info.get('confidence', 0) > best_confidence:
                    best_frame = frame_path
                    best_confidence = url_info['confidence']

            except Exception as e:
                self.log_warning(f"Failed to analyze frame {frame_path}: {e}")
                continue

        return best_frame

    def _discover_website_from_frames(self, video_id: str, frame_paths: List[Path], _tip: Dict[str, Any]) -> bool:
        """Discover website URL from video frames using gpt-4.1-mini Vision.

        Args:
            video_id: YouTube video ID
            frame_paths: List of frame paths to analyze
            _tip: Placeholder tip record (unused, kept for interface compatibility)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.log_info(f"Discovering website from frames for {video_id}")

            # Analyze all frames for website URLs
            discovered_websites = self._analyze_frames_for_urls(frame_paths)

            # Create appropriate database entry based on discoveries
            self._create_discovery_database_entry(video_id, frame_paths, discovered_websites)

            # Clean up frame files if retention is disabled
            if not self.retain_frames:
                self._cleanup_frames(frame_paths)
            return True

        except Exception as e:
            self.log_error(f"Failed to discover website from frames: {e}")
            if not self.retain_frames:
                self._cleanup_frames(frame_paths)
            return False

    def _analyze_frames_for_urls(self, frame_paths: List[Path]) -> List[Dict[str, Any]]:
        """Analyze all frames for website URLs with early termination support.

        Args:
            frame_paths: List of frame paths to analyze

        Returns:
            List of discovered websites with metadata
        """
        discovered_websites = []

        for i, frame_path in enumerate(frame_paths):
            try:
                self.log_debug(f"Analyzing frame {i+1}/{len(frame_paths)}: {frame_path.name}")

                # Encode frame as base64
                with open(frame_path, 'rb') as f:
                    image_data = base64.b64encode(f.read()).decode('utf-8')

                # Use gpt-4.1-mini Vision to discover any website URLs
                url_info = self._discover_url_from_frame(image_data)

                if url_info and url_info.get('url_detected'):
                    confidence = url_info.get('confidence', 0)
                    discovered_websites.append({
                        'url': url_info.get('detected_text', ''),
                        'confidence': confidence,
                        'description': url_info.get('description', ''),
                        'frame_path': frame_path,
                        'frame_index': i
                    })

                    self.log_debug(f"Found URL in frame {i}: {url_info.get('detected_text', '')} (confidence: {confidence}%)")

                    # Check for early termination
                    if self._should_terminate_early(confidence):
                        self.log_info(f"Early termination: High confidence URL found in frame {i} with {confidence}% confidence")
                        break
                else:
                    self.log_debug(f"No URL detected in frame {i}")

            except Exception as e:
                self.log_warning(f"Failed to analyze frame {frame_path}: {e}")
                continue

        return discovered_websites

    def _should_terminate_early(self, confidence: float) -> bool:
        """Determine if early termination should be used based on confidence.

        Args:
            confidence: Current discovery confidence

        Returns:
            True if early termination should be used
        """
        return MetadataManager.should_use_early_termination(
            confidence=confidence,
            confidence_threshold=self.confidence_threshold,
            early_termination_enabled=self.multi_frame_enabled and self.early_termination
        )

    def _create_discovery_database_entry(self, video_id: str, frame_paths: List[Path], discovered_websites: List[Dict[str, Any]]) -> None:
        """Create appropriate database entry based on discovery results.

        Args:
            video_id: YouTube video ID
            frame_paths: List of frame paths analyzed
            discovered_websites: List of discovered websites
        """
        if not discovered_websites:
            self._create_fallback_entry(video_id, frame_paths)
            return

        best_discovery = MetadataManager.get_best_discovery(discovered_websites)
        if not best_discovery:
            self._create_fallback_entry(video_id, frame_paths)
            return

        # Create metadata for the discovery
        metadata = MetadataManager.create_frame_metadata(
            multi_frame_enabled=self.multi_frame_enabled,
            total_frames=len(frame_paths),
            successful_frame_index=best_discovery.get('frame_index', 0),
            confidence=best_discovery['confidence'],
            frame_intervals=self.frame_intervals,
            early_termination_used=self._should_terminate_early(best_discovery['confidence']),
            all_discoveries=discovered_websites
        )

        if best_discovery['confidence'] > 50:  # Minimum confidence threshold
            self._create_success_entry(video_id, frame_paths, best_discovery, metadata)
        else:
            self._create_low_confidence_entry(video_id, frame_paths, best_discovery, metadata)

    def _create_success_entry(self, video_id: str, frame_paths: List[Path], best_discovery: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        """Create database entry for successful website discovery.

        Args:
            video_id: YouTube video ID
            frame_paths: List of frame paths analyzed
            best_discovery: Best discovery result
            metadata: Frame analysis metadata
        """
        website_info = self._extract_website_info_from_transcript(video_id, best_discovery['url'])

        tip = MetadataManager.create_success_tip(
            best_discovery=best_discovery,
            website_info=website_info,
            frame_paths=frame_paths,
            metadata=metadata
        )

        self.db_manager.insert_tips(video_id, [tip])
        self.log_info(f"Discovered website {best_discovery['url']} with {best_discovery['confidence']}% confidence")

    def _create_low_confidence_entry(self, video_id: str, frame_paths: List[Path], best_discovery: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        """Create database entry for low confidence discovery.

        Args:
            video_id: YouTube video ID
            frame_paths: List of frame paths analyzed
            best_discovery: Best discovery result
            metadata: Frame analysis metadata
        """
        website_info = self._extract_website_info_from_transcript_fallback(video_id)

        tip = MetadataManager.create_low_confidence_tip(
            best_discovery=best_discovery,
            website_info=website_info,
            frame_paths=frame_paths,
            metadata=metadata
        )

        self.db_manager.insert_tips(video_id, [tip])
        self.log_debug(f"Low confidence discovery ({best_discovery['confidence']}%) saved to database")

    def _create_fallback_entry(self, video_id: str, frame_paths: List[Path]) -> None:
        """Create database entry when no website is discovered.

        Args:
            video_id: YouTube video ID
            frame_paths: List of frame paths analyzed
        """
        self.log_debug(f"No websites discovered in frames for {video_id}, creating fallback entry")
        website_info = self._extract_website_info_from_transcript_fallback(video_id)

        metadata = MetadataManager.create_frame_metadata(
            multi_frame_enabled=self.multi_frame_enabled,
            total_frames=len(frame_paths),
            successful_frame_index=None,
            confidence=0,
            frame_intervals=self.frame_intervals,
            early_termination_used=False,
            all_discoveries=[]
        )

        tip = MetadataManager.create_fallback_tip(
            website_info=website_info,
            frame_paths=frame_paths,
            metadata=metadata
        )

        self.db_manager.insert_tips(video_id, [tip])
        self.log_info(f"Created fallback database entry for {video_id} with transcript analysis")

    def _discover_url_from_frame(self, image_data: str) -> Optional[Dict[str, Any]]:
        """Use gpt-4.1-mini Vision to discover any website URLs in a frame.

        Args:
            image_data: Base64 encoded image data

        Returns:
            Discovery result with URL info or None
        """
        try:
            system_prompt = """You are an expert at analyzing video frames to detect website URLs and text.

Look for any visible URLs, website names, domain names, or text that appears to be a website address.

Return a JSON object with:
{
  "url_detected": true/false,
  "detected_text": "the actual URL or website name you can see (e.g., example.com, https://site.com)",
  "confidence": 0-100 (how confident you are that this is a website URL),
  "description": "brief description of what you see and where the URL appears"
}

Focus on finding actual website addresses, not just mentions of websites."""

            user_prompt = "Analyze this video frame and look for any website URLs, domain names, or website addresses that are visible on screen."

            response = self.openai_client.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": user_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()
            return self.openai_client._parse_vision_response(content)

        except Exception as e:
            self.log_warning(f"Failed to discover URL from frame: {e}")
            return None

    def _cleanup_frames(self, frame_paths: List[Path]):
        """Clean up extracted frame files.

        Args:
            frame_paths: List of frame paths to clean up
        """
        for frame_path in frame_paths:
            try:
                if frame_path.exists():
                    frame_path.unlink()
            except Exception as e:
                self.log_warning(f"Failed to cleanup frame {frame_path}: {e}")
    
    def _extract_frames(self, video_path: Path, website: str) -> List[Path]:
        """Extract frames from video around website mentions or 'this' trigger words.

        Args:
            video_path: Path to video file
            website: Website name to look for

        Returns:
            List of extracted frame paths
        """
        if not cv2:
            logger.warning("OpenCV not available for frame extraction")
            return []

        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                logger.error(f"Cannot open video: {video_path}")
                return []

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps

            frame_paths = []
            frames_dir = Path("data/raw/frames")
            frames_dir.mkdir(parents=True, exist_ok=True)

            # Get video ID from video path for transcript lookup
            video_id = video_path.stem.replace('video_', '')

            # Use transcript timing for precise frame extraction if enabled and available
            if self.use_transcript_timing and website == 'unknown_website':
                timestamps = self._get_this_trigger_timestamps(video_id)
                if timestamps:
                    base_timestamp = timestamps[0]

                    # Multi-frame extraction if enabled
                    if self.multi_frame_enabled:
                        self.log_debug(f"Multi-frame extraction enabled: extracting {len(self.frame_intervals)} frames")

                        for i, interval in enumerate(self.frame_intervals):
                            timestamp = base_timestamp + interval

                            # Ensure timestamp doesn't exceed video duration
                            if timestamp <= duration:
                                frame_number = int(timestamp * fps)
                                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                                ret, frame = cap.read()

                                if ret:
                                    # Include frame index in filename for multi-frame identification
                                    frame_filename = f"frame_{video_path.stem}_{website.replace('.', '_')}_{int(base_timestamp):03d}_{i:02d}.jpg"
                                    frame_path = frames_dir / frame_filename

                                    # Save frame with specified quality
                                    cv2.imwrite(
                                        str(frame_path),
                                        frame,
                                        [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
                                    )

                                    frame_paths.append(frame_path)
                                    self.log_debug(f"Extracted frame {i} at timestamp {timestamp}s (+{interval}s from base)")
                                else:
                                    self.log_warning(f"Failed to extract frame {i} at timestamp {timestamp}s")
                            else:
                                self.log_warning(f"Timestamp {timestamp}s exceeds video duration {duration}s, skipping frame {i}")

                        self.log_debug(f"Extracted {len(frame_paths)} frames at intervals {self.frame_intervals} for {website}")
                    else:
                        # Original single frame extraction logic
                        timestamp = base_timestamp
                        frame_number = int(timestamp * fps)

                        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
                        ret, frame = cap.read()

                        if ret:
                            frame_filename = f"frame_{video_path.stem}_{website.replace('.', '_')}_{int(timestamp):03d}.jpg"
                            frame_path = frames_dir / frame_filename

                            # Save frame with specified quality
                            cv2.imwrite(
                                str(frame_path),
                                frame,
                                [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
                            )

                            frame_paths.append(frame_path)
                            self.log_debug(f"Extracted 1 frame at timestamp {timestamp}s for {website}")
                else:
                    self.log_debug(f"No 'this' timestamps found, using fallback extraction")
                    # Fallback to simple extraction if no timestamps found
                    frame_paths = self._extract_frames_simple(cap, video_path, website, duration, fps)
            else:
                # Use simple interval-based extraction for known websites or when timing disabled
                frame_paths = self._extract_frames_simple(cap, video_path, website, duration, fps)

            cap.release()
            self.log_debug(f"Extracted {len(frame_paths)} frames for {website}")
            return frame_paths

        except Exception as e:
            self.log_error(f"Failed to extract frames: {e}")
            return []

    def _get_this_trigger_timestamps(self, video_id: str) -> List[float]:
        """Get exact timestamps where 'this' trigger word appears using AssemblyAI word data.

        Args:
            video_id: YouTube video ID

        Returns:
            List of timestamps (in seconds) where 'this' appears
        """
        try:
            # Get video with word-level timing data
            video = self.db_manager.get_video(video_id)
            if not video:
                self.log_debug(f"No video found for timestamp extraction: {video_id}")
                return []

            # Try to get timing data first, fallback to old method
            transcript_data = video.get('transcript_data')
            if transcript_data:
                if isinstance(transcript_data, str):
                    import json
                    transcript_data = json.loads(transcript_data)

                timestamps = []

                # Use actual word timing data
                if 'words' in transcript_data and transcript_data['words']:
                    for word in transcript_data['words']:
                        if word['text'].lower() == 'this':
                            # Convert milliseconds to seconds for frame extraction
                            timestamp_seconds = word['start'] / 1000.0
                            timestamps.append(timestamp_seconds)
                            self.log_debug(f"Found 'this' at precise timestamp: {timestamp_seconds}s")
                            break  # Get first occurrence only

                    return timestamps
                else:
                    self.log_debug(f"No word timing data available for {video_id}, using fallback")
                    return self._get_this_trigger_timestamps_fallback(video_id)
            else:
                # Fallback to old estimation method for backward compatibility
                self.log_debug(f"No timing data available for {video_id}, using estimation")
                return self._get_this_trigger_timestamps_fallback(video_id)

        except Exception as e:
            self.log_error(f"Failed to get precise 'this' timestamps: {e}")
            return self._get_this_trigger_timestamps_fallback(video_id)

    def _get_this_trigger_timestamps_fallback(self, video_id: str) -> List[float]:
        """Fallback to old estimation method for backward compatibility.

        Args:
            video_id: YouTube video ID

        Returns:
            List of estimated timestamps (in seconds) where 'this' appears
        """
        try:
            # Get video transcript
            video = self.db_manager.get_video(video_id)
            if not video or not video.get('transcript'):
                self.log_debug(f"No transcript available for timestamp extraction: {video_id}")
                return []

            transcript = video['transcript'].lower()

            # Return estimated timestamps based on word position
            words = transcript.split()
            timestamps = []

            # Estimate timing: assume average speaking rate of 150 words per minute
            words_per_second = 150 / 60  # ~2.5 words per second

            for i, word in enumerate(words):
                if 'this' in word:
                    timestamp = i / words_per_second
                    timestamps.append(timestamp)
                    # Only return first occurrence for optimization
                    break

            self.log_debug(f"Found {len(timestamps)} 'this' timestamps (estimated) for {video_id}")
            return timestamps

        except Exception as e:
            self.log_error(f"Failed to get fallback 'this' timestamps for {video_id}: {e}")
            return []

    def _extract_frames_simple(self, cap, video_path: Path, website: str, duration: float, fps: float) -> List[Path]:
        """Simple interval-based frame extraction (fallback method).

        Args:
            cap: OpenCV VideoCapture object
            video_path: Path to video file
            website: Website name
            duration: Video duration in seconds
            fps: Video frames per second

        Returns:
            List of extracted frame paths
        """
        frame_paths = []
        frames_dir = Path("data/raw/frames")

        # Extract frames at regular intervals
        interval = max(1, duration / min(self.max_frames, 10))

        for i in range(min(self.max_frames, int(duration / interval))):
            timestamp = i * interval
            frame_number = int(timestamp * fps)

            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()

            if ret:
                frame_filename = f"frame_{video_path.stem}_{website.replace('.', '_')}_{i:03d}.jpg"
                frame_path = frames_dir / frame_filename

                # Save frame with specified quality
                cv2.imwrite(
                    str(frame_path),
                    frame,
                    [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality]
                )

                frame_paths.append(frame_path)

        return frame_paths

    def _update_tip_frame(self, video_id: str, website: str, frame_path: str):
        """Update tip record with frame path.

        Args:
            video_id: YouTube video ID
            website: Website name
            frame_path: Path to best frame
        """
        try:
            with self.db_manager.get_connection() as conn:
                conn.execute("""
                    UPDATE tips
                    SET frame_path = ?
                    WHERE video_id = ? AND website = ?
                """, (frame_path, video_id, website))
                conn.commit()
        except Exception as e:
            self.log_error(f"Failed to update tip frame for {video_id}/{website}: {e}")

    def _cleanup_video(self, video_path: Path):
        """Clean up downloaded video file.

        Args:
            video_path: Path to video file
        """
        try:
            if video_path and video_path.exists():
                video_path.unlink()
                self.log_debug(f"Cleaned up video: {video_path}")
        except Exception as e:
            self.log_error(f"Failed to cleanup video {video_path}: {e}")
    
    def get_vision_complete_videos(self) -> List[Dict[str, Any]]:
        """Get videos that have completed vision analysis.

        Returns:
            List of videos with 'vision_done' status
        """
        return self.db_manager.get_videos_by_status('vision_done')

    def _extract_website_info_from_transcript(self, video_id: str, website_url: str) -> Dict[str, str]:
        """Extract website information from transcript with specific website context.

        Args:
            video_id: YouTube video ID
            website_url: Discovered website URL

        Returns:
            Dictionary with 'use' and 'details' fields
        """
        try:
            # Get video transcript
            video = self.db_manager.get_video(video_id)
            if not video or not video.get('transcript'):
                self.log_debug(f"No transcript available for website info extraction: {video_id}")
                return {'use': f"Website mentioned: {website_url}", 'details': "No transcript available for detailed analysis"}

            transcript = video['transcript']

            # Use OpenAI to extract specific information about this website
            website_info = self.openai_client.extract_website_info_with_context(transcript, website_url)

            if website_info:
                return {
                    'use': website_info.get('use', f"Website mentioned: {website_url}"),
                    'details': website_info.get('details', "Additional details not available from transcript")
                }
            else:
                return {
                    'use': f"Website mentioned: {website_url}",
                    'details': "Unable to extract detailed information from transcript"
                }

        except Exception as e:
            self.log_error(f"Failed to extract website info from transcript for {video_id}/{website_url}: {e}")
            return {
                'use': f"Website mentioned: {website_url}",
                'details': f"Error extracting details: {str(e)}"
            }

    def _extract_website_info_from_transcript_fallback(self, video_id: str) -> Dict[str, str]:
        """Extract general website information from transcript when no specific URL is found.

        Args:
            video_id: YouTube video ID

        Returns:
            Dictionary with 'use' and 'details' fields based on transcript analysis
        """
        try:
            # Get video transcript
            video = self.db_manager.get_video(video_id)
            if not video or not video.get('transcript'):
                self.log_debug(f"No transcript available for fallback extraction: {video_id}")
                return {
                    'use': "Website mentioned in video",
                    'details': "No transcript available for detailed analysis"
                }

            transcript = video['transcript']

            # Use OpenAI to extract general website information from transcript
            website_info = self.openai_client.extract_general_website_info(transcript)

            if website_info:
                return {
                    'use': website_info.get('use', "Website or tool mentioned in video"),
                    'details': website_info.get('details', "Additional details extracted from transcript analysis")
                }
            else:
                return {
                    'use': "Website or tool mentioned in video",
                    'details': "Website reference detected but specific details not available from transcript"
                }

        except Exception as e:
            self.log_error(f"Failed to extract fallback website info from transcript for {video_id}: {e}")
            return {
                'use': "Website mentioned in video",
                'details': f"Error extracting details: {str(e)}"
            }
