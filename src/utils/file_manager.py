"""
File management utilities for the scraper.

Provides centralized file operations with proper error handling, cleanup,
and path management.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from contextlib import contextmanager

from ..exceptions import FileOperationError

logger = logging.getLogger(__name__)


class FileManager:
    """Centralized file management with error handling and cleanup."""
    
    def __init__(self, base_dir: Union[str, Path] = "."):
        """Initialize file manager.
        
        Args:
            base_dir: Base directory for all file operations
        """
        self.base_dir = Path(base_dir)
        self.temp_files: List[Path] = []
    
    def ensure_directory(self, path: Union[str, Path]) -> Path:
        """Ensure directory exists, creating it if necessary.
        
        Args:
            path: Directory path (relative to base_dir or absolute)
            
        Returns:
            Resolved directory path
            
        Raises:
            FileOperationError: If directory creation fails
        """
        try:
            if not Path(path).is_absolute():
                path = self.base_dir / path
            
            path = Path(path)
            path.mkdir(parents=True, exist_ok=True)
            
            logger.debug(f"Ensured directory exists: {path}")
            return path
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to create directory: {e}",
                file_path=str(path),
                operation="create_directory"
            )
    
    def save_json(self, data: Dict[str, Any], file_path: Union[str, Path], 
                  ensure_dir: bool = True) -> Path:
        """Save data as JSON file.
        
        Args:
            data: Data to save
            file_path: Path to save file (relative to base_dir or absolute)
            ensure_dir: Whether to create parent directories
            
        Returns:
            Path to saved file
            
        Raises:
            FileOperationError: If save operation fails
        """
        try:
            if not Path(file_path).is_absolute():
                file_path = self.base_dir / file_path
            
            file_path = Path(file_path)
            
            if ensure_dir:
                self.ensure_directory(file_path.parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved JSON file: {file_path}")
            return file_path
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to save JSON file: {e}",
                file_path=str(file_path),
                operation="write"
            )
    
    def load_json(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load data from JSON file.
        
        Args:
            file_path: Path to JSON file (relative to base_dir or absolute)
            
        Returns:
            Loaded data
            
        Raises:
            FileOperationError: If load operation fails
        """
        try:
            if not Path(file_path).is_absolute():
                file_path = self.base_dir / file_path
            
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileOperationError(
                    f"File does not exist: {file_path}",
                    file_path=str(file_path),
                    operation="read"
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded JSON file: {file_path}")
            return data
            
        except json.JSONDecodeError as e:
            raise FileOperationError(
                f"Invalid JSON format: {e}",
                file_path=str(file_path),
                operation="read"
            )
        except Exception as e:
            raise FileOperationError(
                f"Failed to load JSON file: {e}",
                file_path=str(file_path),
                operation="read"
            )
    
    def save_text(self, text: str, file_path: Union[str, Path], 
                  ensure_dir: bool = True) -> Path:
        """Save text to file.
        
        Args:
            text: Text content to save
            file_path: Path to save file (relative to base_dir or absolute)
            ensure_dir: Whether to create parent directories
            
        Returns:
            Path to saved file
            
        Raises:
            FileOperationError: If save operation fails
        """
        try:
            if not Path(file_path).is_absolute():
                file_path = self.base_dir / file_path
            
            file_path = Path(file_path)
            
            if ensure_dir:
                self.ensure_directory(file_path.parent)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            logger.debug(f"Saved text file: {file_path}")
            return file_path
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to save text file: {e}",
                file_path=str(file_path),
                operation="write"
            )
    
    def load_text(self, file_path: Union[str, Path]) -> str:
        """Load text from file.
        
        Args:
            file_path: Path to text file (relative to base_dir or absolute)
            
        Returns:
            File content as string
            
        Raises:
            FileOperationError: If load operation fails
        """
        try:
            if not Path(file_path).is_absolute():
                file_path = self.base_dir / file_path
            
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileOperationError(
                    f"File does not exist: {file_path}",
                    file_path=str(file_path),
                    operation="read"
                )
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            logger.debug(f"Loaded text file: {file_path}")
            return content
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to load text file: {e}",
                file_path=str(file_path),
                operation="read"
            )
    
    def delete_file(self, file_path: Union[str, Path], 
                    missing_ok: bool = True) -> bool:
        """Delete a file.
        
        Args:
            file_path: Path to file to delete (relative to base_dir or absolute)
            missing_ok: If True, don't raise error if file doesn't exist
            
        Returns:
            True if file was deleted, False if it didn't exist
            
        Raises:
            FileOperationError: If deletion fails
        """
        try:
            if not Path(file_path).is_absolute():
                file_path = self.base_dir / file_path
            
            file_path = Path(file_path)
            
            if not file_path.exists():
                if missing_ok:
                    return False
                else:
                    raise FileOperationError(
                        f"File does not exist: {file_path}",
                        file_path=str(file_path),
                        operation="delete"
                    )
            
            file_path.unlink()
            logger.debug(f"Deleted file: {file_path}")
            return True
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to delete file: {e}",
                file_path=str(file_path),
                operation="delete"
            )
    
    def register_temp_file(self, file_path: Union[str, Path]) -> Path:
        """Register a file for automatic cleanup.
        
        Args:
            file_path: Path to temporary file
            
        Returns:
            Resolved file path
        """
        if not Path(file_path).is_absolute():
            file_path = self.base_dir / file_path
        
        file_path = Path(file_path)
        self.temp_files.append(file_path)
        logger.debug(f"Registered temp file: {file_path}")
        return file_path
    
    def cleanup_temp_files(self) -> int:
        """Clean up all registered temporary files.
        
        Returns:
            Number of files cleaned up
        """
        cleaned_count = 0
        
        for file_path in self.temp_files:
            try:
                if file_path.exists():
                    file_path.unlink()
                    cleaned_count += 1
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {file_path}: {e}")
        
        self.temp_files.clear()
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} temporary files")
        
        return cleaned_count
    
    @contextmanager
    def temp_file_context(self, file_path: Union[str, Path]):
        """Context manager for temporary files that are automatically cleaned up.
        
        Args:
            file_path: Path to temporary file
            
        Yields:
            Path to the temporary file
        """
        temp_path = self.register_temp_file(file_path)
        try:
            yield temp_path
        finally:
            try:
                if temp_path.exists():
                    temp_path.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")
    
    def get_file_size(self, file_path: Union[str, Path]) -> int:
        """Get file size in bytes.
        
        Args:
            file_path: Path to file
            
        Returns:
            File size in bytes
            
        Raises:
            FileOperationError: If file doesn't exist or can't be accessed
        """
        try:
            if not Path(file_path).is_absolute():
                file_path = self.base_dir / file_path
            
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileOperationError(
                    f"File does not exist: {file_path}",
                    file_path=str(file_path),
                    operation="stat"
                )
            
            return file_path.stat().st_size
            
        except Exception as e:
            raise FileOperationError(
                f"Failed to get file size: {e}",
                file_path=str(file_path),
                operation="stat"
            )
