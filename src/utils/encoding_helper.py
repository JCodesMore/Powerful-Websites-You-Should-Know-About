"""
UTF-8 encoding utilities for the scraper.

Provides consistent encoding handling across all file operations,
with special focus on fixing CSV export encoding issues.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import unicodedata

logger = logging.getLogger(__name__)


class EncodingHelper:
    """Handles UTF-8 encoding operations and text normalization."""
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text to handle encoding issues.
        
        Args:
            text: Input text that may have encoding issues
            
        Returns:
            Normalized UTF-8 text
        """
        if not text:
            return ""
            
        # Convert to string if not already
        text = str(text)
        
        # Normalize Unicode characters
        normalized = unicodedata.normalize('NFKC', text)
        
        # Fix common encoding issues
        normalized = EncodingHelper._fix_common_encoding_issues(normalized)
        
        return normalized.strip()
    
    @staticmethod
    def _fix_common_encoding_issues(text: str) -> str:
        """Fix common encoding issues in text.
        
        Args:
            text: Input text with potential encoding issues
            
        Returns:
            Text with encoding issues fixed
        """
        # Common encoding issue mappings (using escape sequences to avoid encoding issues)
        encoding_fixes = {
            '\u00e2\u0080\u0099': "'",  # Right single quotation mark (â€™ → ')
            '\u00e2\u0080\u009c': '"',  # Left double quotation mark (â€œ → ")
            '\u00e2\u0080\u009d': '"',  # Right double quotation mark (â€ → ")
            '\u00e2\u0080\u0093': '–',  # En dash (â€" → –)
            '\u00e2\u0080\u0094': '—',  # Em dash (â€" → —)
            '\u00e2\u0080\u00a6': '…',  # Horizontal ellipsis (â€¦ → …)
            '\u00c3\u00a1': 'á',       # Latin small letter a with acute (Ã¡ → á)
            '\u00c3\u00a9': 'é',       # Latin small letter e with acute (Ã© → é)
            '\u00c3\u00ad': 'í',       # Latin small letter i with acute (Ã­ → í)
            '\u00c3\u00b3': 'ó',       # Latin small letter o with acute (Ã³ → ó)
            '\u00c3\u00ba': 'ú',       # Latin small letter u with acute (Ãº → ú)
        }
        
        for bad_encoding, correct_char in encoding_fixes.items():
            text = text.replace(bad_encoding, correct_char)
            
        return text
    
    @staticmethod
    def clean_csv_field(value: Any) -> str:
        """Clean and prepare a field value for CSV export.
        
        Args:
            value: Field value to clean
            
        Returns:
            Cleaned string value safe for CSV export
        """
        if value is None:
            return ""
            
        # Convert to string and normalize
        text = EncodingHelper.normalize_text(str(value))
        
        # Remove newlines and extra whitespace
        text = ' '.join(text.split())
        
        # Escape quotes for CSV (handled by csv module, but ensure consistency)
        return text
    
    @staticmethod
    def write_csv_safely(
        data: List[Dict[str, Any]], 
        output_path: Path, 
        fieldnames: List[str],
        include_headers: bool = True
    ) -> None:
        """Write data to CSV file with proper UTF-8 encoding.
        
        Args:
            data: List of data records
            output_path: Path to output CSV file
            fieldnames: CSV column names
            include_headers: Whether to include header row
            
        Raises:
            IOError: If file writing fails
        """
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(
                    csvfile,
                    fieldnames=fieldnames,
                    extrasaction='ignore'
                )
                
                if include_headers:
                    writer.writeheader()
                
                for record in data:
                    # Clean all fields in the record
                    cleaned_record = {}
                    for field in fieldnames:
                        cleaned_record[field] = EncodingHelper.clean_csv_field(
                            record.get(field, '')
                        )
                    writer.writerow(cleaned_record)
                    
            logger.debug(f"CSV written safely to {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to write CSV to {output_path}: {e}")
            raise
    
    @staticmethod
    def validate_utf8_text(text: str) -> bool:
        """Validate that text is properly UTF-8 encoded.
        
        Args:
            text: Text to validate
            
        Returns:
            True if text is valid UTF-8, False otherwise
        """
        try:
            text.encode('utf-8').decode('utf-8')
            return True
        except (UnicodeEncodeError, UnicodeDecodeError):
            return False
    
    @staticmethod
    def safe_filename(filename: str) -> str:
        """Create a safe filename by removing/replacing problematic characters.
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename for filesystem use
        """
        # Normalize the filename
        safe_name = EncodingHelper.normalize_text(filename)
        
        # Replace problematic characters
        problematic_chars = '<>:"/\\|?*'
        for char in problematic_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Remove leading/trailing dots and spaces
        safe_name = safe_name.strip('. ')
        
        # Ensure it's not empty
        if not safe_name:
            safe_name = "unnamed_file"
            
        return safe_name
