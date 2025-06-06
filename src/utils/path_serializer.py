"""
Path object JSON serialization utilities.

Handles conversion between Path objects and JSON-serializable formats
for database storage and API communication.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Union

logger = logging.getLogger(__name__)


class PathSerializer:
    """Handles serialization and deserialization of Path objects."""
    
    @staticmethod
    def serialize_path(path: Union[Path, str, None]) -> str:
        """Convert a Path object to a JSON-serializable string.
        
        Args:
            path: Path object, string, or None
            
        Returns:
            String representation of the path
        """
        if path is None:
            return ""
        
        if isinstance(path, Path):
            return str(path)
        
        return str(path)
    
    @staticmethod
    def serialize_path_list(paths: List[Union[Path, str]]) -> str:
        """Convert a list of Path objects to JSON string.
        
        Args:
            paths: List of Path objects or strings
            
        Returns:
            JSON string representation of the path list
        """
        if not paths:
            return "[]"
        
        try:
            path_strings = [PathSerializer.serialize_path(path) for path in paths]
            return json.dumps(path_strings)
        except Exception as e:
            logger.error(f"Failed to serialize path list: {e}")
            return "[]"
    
    @staticmethod
    def deserialize_path(path_str: str) -> Path:
        """Convert a string back to a Path object.
        
        Args:
            path_str: String representation of a path
            
        Returns:
            Path object
        """
        if not path_str:
            return Path()
        
        return Path(path_str)
    
    @staticmethod
    def deserialize_path_list(paths_json: str) -> List[Path]:
        """Convert a JSON string back to a list of Path objects.
        
        Args:
            paths_json: JSON string representation of path list
            
        Returns:
            List of Path objects
        """
        if not paths_json:
            return []
        
        try:
            path_strings = json.loads(paths_json)
            return [Path(path_str) for path_str in path_strings]
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to deserialize path list: {e}")
            return []
    
    @staticmethod
    def clean_metadata_for_json(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean metadata dictionary to make it JSON-serializable.
        
        Args:
            metadata: Metadata dictionary that may contain Path objects
            
        Returns:
            Cleaned metadata dictionary
        """
        if not metadata:
            return {}
        
        try:
            cleaned = {}
            
            for key, value in metadata.items():
                if isinstance(value, Path):
                    cleaned[key] = str(value)
                elif isinstance(value, list):
                    cleaned[key] = PathSerializer._clean_list_for_json(value)
                elif isinstance(value, dict):
                    cleaned[key] = PathSerializer.clean_metadata_for_json(value)
                else:
                    cleaned[key] = value
            
            return cleaned
            
        except Exception as e:
            logger.error(f"Failed to clean metadata for JSON: {e}")
            return {}
    
    @staticmethod
    def _clean_list_for_json(items: List[Any]) -> List[Any]:
        """Clean a list to make it JSON-serializable.
        
        Args:
            items: List that may contain Path objects
            
        Returns:
            Cleaned list
        """
        cleaned_items = []
        
        for item in items:
            if isinstance(item, Path):
                cleaned_items.append(str(item))
            elif isinstance(item, dict):
                cleaned_items.append(PathSerializer.clean_metadata_for_json(item))
            elif isinstance(item, list):
                cleaned_items.append(PathSerializer._clean_list_for_json(item))
            else:
                cleaned_items.append(item)
        
        return cleaned_items
    
    @staticmethod
    def serialize_frame_metadata(metadata: Dict[str, Any]) -> str:
        """Serialize frame analysis metadata for database storage.
        
        Args:
            metadata: Frame analysis metadata dictionary
            
        Returns:
            JSON string representation
        """
        if not metadata:
            return "{}"
        
        try:
            # Clean the metadata to handle Path objects
            cleaned_metadata = PathSerializer.clean_metadata_for_json(metadata)
            return json.dumps(cleaned_metadata)
        except Exception as e:
            logger.error(f"Failed to serialize frame metadata: {e}")
            return "{}"
    
    @staticmethod
    def deserialize_frame_metadata(metadata_json: str) -> Dict[str, Any]:
        """Deserialize frame analysis metadata from database.
        
        Args:
            metadata_json: JSON string representation
            
        Returns:
            Metadata dictionary
        """
        if not metadata_json:
            return {}
        
        try:
            return json.loads(metadata_json)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Failed to deserialize frame metadata: {e}")
            return {}
