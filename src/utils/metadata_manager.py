"""
Multi-frame metadata handling utilities.

Manages metadata for multi-frame extraction including confidence tracking,
frame analysis results, and early termination logic.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .path_serializer import PathSerializer

logger = logging.getLogger(__name__)


class MetadataManager:
    """Manages multi-frame extraction metadata."""
    
    @staticmethod
    def create_frame_metadata(
        multi_frame_enabled: bool,
        total_frames: int,
        successful_frame_index: Optional[int],
        confidence: float,
        frame_intervals: List[float],
        early_termination_used: bool,
        all_discoveries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create standardized frame analysis metadata.
        
        Args:
            multi_frame_enabled: Whether multi-frame extraction was used
            total_frames: Total number of frames analyzed
            successful_frame_index: Index of successful frame (None if no success)
            confidence: Confidence score of best discovery
            frame_intervals: Time intervals used for frame extraction
            early_termination_used: Whether early termination was triggered
            all_discoveries: List of all discoveries made
            
        Returns:
            Standardized metadata dictionary
        """
        metadata = {
            'multi_frame_enabled': multi_frame_enabled,
            'total_frames_analyzed': total_frames,
            'successful_frame_index': successful_frame_index,
            'confidence': confidence,
            'frame_intervals': frame_intervals,
            'early_termination_used': early_termination_used,
            'all_discoveries': MetadataManager._clean_discoveries(all_discoveries)
        }
        
        return metadata
    
    @staticmethod
    def _clean_discoveries(discoveries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Clean discovery data to ensure JSON serialization compatibility.
        
        Args:
            discoveries: List of discovery dictionaries
            
        Returns:
            Cleaned discovery list
        """
        cleaned_discoveries = []
        
        for discovery in discoveries:
            cleaned_discovery = {}
            for key, value in discovery.items():
                if isinstance(value, Path):
                    cleaned_discovery[key] = str(value)
                else:
                    cleaned_discovery[key] = value
            cleaned_discoveries.append(cleaned_discovery)
        
        return cleaned_discoveries
    
    @staticmethod
    def should_use_early_termination(
        confidence: float,
        confidence_threshold: float,
        early_termination_enabled: bool
    ) -> bool:
        """Determine if early termination should be used.
        
        Args:
            confidence: Current discovery confidence
            confidence_threshold: Threshold for early termination
            early_termination_enabled: Whether early termination is enabled
            
        Returns:
            True if early termination should be used
        """
        return (
            early_termination_enabled and 
            confidence >= confidence_threshold
        )
    
    @staticmethod
    def get_best_discovery(discoveries: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get the best discovery from a list based on confidence.
        
        Args:
            discoveries: List of discovery dictionaries
            
        Returns:
            Best discovery or None if no discoveries
        """
        if not discoveries:
            return None
        
        return max(discoveries, key=lambda x: x.get('confidence', 0))
    
    @staticmethod
    def create_success_tip(
        best_discovery: Dict[str, Any],
        website_info: Dict[str, str],
        frame_paths: List[Path],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a tip record for successful website discovery.
        
        Args:
            best_discovery: Best discovery from frame analysis
            website_info: Extracted website information
            frame_paths: List of all frame paths
            metadata: Frame analysis metadata
            
        Returns:
            Complete tip record
        """
        tip = {
            'website': best_discovery['url'],
            'use': website_info.get('use', f"Website discovered in video: {best_discovery['url']}"),
            'details': website_info.get('details', f"Discovered from video frame: {best_discovery['description']}"),
            'frame_path': str(best_discovery['frame_path'])
        }
        
        # Add multi-frame metadata if applicable
        if metadata.get('multi_frame_enabled') and len(frame_paths) > 1:
            tip['frame_paths'] = frame_paths
            tip['successful_frame_index'] = best_discovery.get('frame_index', 0)
            tip['frame_analysis_metadata'] = metadata
        
        return tip
    
    @staticmethod
    def create_low_confidence_tip(
        best_discovery: Dict[str, Any],
        website_info: Dict[str, str],
        frame_paths: List[Path],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a tip record for low confidence discovery.
        
        Args:
            best_discovery: Best discovery from frame analysis
            website_info: Extracted website information
            frame_paths: List of all frame paths
            metadata: Frame analysis metadata
            
        Returns:
            Complete tip record for low confidence discovery
        """
        confidence = best_discovery.get('confidence', 0)
        
        tip = {
            'website': f"Low confidence: {best_discovery['url']}",
            'use': website_info.get('use', "Website mentioned but uncertain identification"),
            'details': website_info.get('details', f"Low confidence discovery ({confidence}%): {best_discovery['description']}"),
            'frame_path': str(best_discovery['frame_path'])
        }
        
        # Add multi-frame metadata if applicable
        if metadata.get('multi_frame_enabled') and len(frame_paths) > 1:
            tip['frame_paths'] = frame_paths
            tip['successful_frame_index'] = best_discovery.get('frame_index', 0)
            tip['frame_analysis_metadata'] = metadata
        
        return tip
    
    @staticmethod
    def create_fallback_tip(
        website_info: Dict[str, str],
        frame_paths: List[Path],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a tip record when no website is discovered.
        
        Args:
            website_info: Extracted website information from transcript
            frame_paths: List of all frame paths
            metadata: Frame analysis metadata
            
        Returns:
            Complete fallback tip record
        """
        frame_path = str(frame_paths[0]) if frame_paths else ""
        
        tip = {
            'website': "Not found",
            'use': website_info.get('use', "Website mentioned but not visually identified"),
            'details': website_info.get('details', "Website reference detected in transcript but URL not found in video frames"),
            'frame_path': frame_path
        }
        
        # Add multi-frame metadata if applicable
        if metadata.get('multi_frame_enabled') and len(frame_paths) > 1:
            tip['frame_paths'] = frame_paths
            tip['successful_frame_index'] = None  # No successful detection
            tip['frame_analysis_metadata'] = metadata
        
        return tip
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> bool:
        """Validate frame analysis metadata structure.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            True if metadata is valid, False otherwise
        """
        required_fields = [
            'multi_frame_enabled',
            'total_frames_analyzed',
            'confidence',
            'frame_intervals',
            'early_termination_used',
            'all_discoveries'
        ]
        
        try:
            for field in required_fields:
                if field not in metadata:
                    logger.warning(f"Missing required metadata field: {field}")
                    return False
            
            # Validate data types
            if not isinstance(metadata['multi_frame_enabled'], bool):
                return False
            
            if not isinstance(metadata['total_frames_analyzed'], int):
                return False
            
            if not isinstance(metadata['confidence'], (int, float)):
                return False
            
            if not isinstance(metadata['frame_intervals'], list):
                return False
            
            if not isinstance(metadata['early_termination_used'], bool):
                return False
            
            if not isinstance(metadata['all_discoveries'], list):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating metadata: {e}")
            return False
