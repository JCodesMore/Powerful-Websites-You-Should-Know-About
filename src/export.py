"""
Phase 5: CSV Export

Exports extracted tips to CSV files for use in Notion, Sheets, etc.
"""

import logging
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .db import DatabaseManager
from .utils import FileManager, DataValidator, EncodingHelper
from .utils.logging_helper import LoggingMixin
from .exceptions import ExportError, ValidationError

logger = logging.getLogger(__name__)


class TipsExporter(LoggingMixin):
    """Exports tips to CSV format."""

    def __init__(self, db_manager: DatabaseManager, config: Dict[str, Any]):
        """Initialize tips exporter.

        Args:
            db_manager: Database manager instance
            config: Configuration dictionary
        """
        super().__init__()
        self.db_manager = db_manager
        self.config = config

        # Initialize utilities
        self.file_manager = FileManager()
        self.validator = DataValidator()

        # Export settings
        self.export_config = config.get('export', {})
        self.csv_config = self.export_config.get('csv', {})
        self.include_headers = self.csv_config.get('include_headers', True)
        self.date_format = self.csv_config.get('date_format', '%Y%m%d_%H%M%S')
        self.columns = self.csv_config.get('columns', [
            'video_id', 'video_url', 'video_title', 'published_at',
            'website', 'use', 'details', 'frame_path'
        ])

        # Set logging context
        self.set_logging_context({
            'component': 'TipsExporter'
        })
    
    def export_tips(self, output_filename: str = None) -> bool:
        """Export all tips to CSV file.

        Args:
            output_filename: Custom filename (optional)

        Returns:
            True if successful, False otherwise

        Raises:
            ExportError: If export fails
        """
        try:
            self.log_info("Starting tips export to CSV")

            # Get all tips from database
            tips = self.db_manager.get_all_tips()

            if not tips:
                self.log_warning("No tips found to export")
                return True

            # Generate and validate filename
            filename = self._generate_filename(output_filename, "tips")

            # Export to CSV
            output_path = self._export_to_csv(tips, filename)

            self.log_info(f"Successfully exported {len(tips)} tips to {output_path}")
            return True

        except Exception as e:
            self.log_error(f"Failed to export tips: {e}")
            return False

    def _generate_filename(self, custom_filename: str = None, prefix: str = "export") -> str:
        """Generate export filename.

        Args:
            custom_filename: Custom filename if provided
            prefix: Filename prefix

        Returns:
            Generated filename
        """
        if custom_filename:
            # Validate and sanitize custom filename
            return self.validator.sanitize_filename(custom_filename)

        # Generate timestamp-based filename
        timestamp = datetime.now().strftime(self.date_format)
        return f"{prefix}_{timestamp}.csv"

    def _export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> Path:
        """Export data to CSV file.

        Args:
            data: Data to export
            filename: Output filename

        Returns:
            Path to exported file

        Raises:
            ExportError: If export fails
        """
        try:
            # Ensure exports directory exists
            output_path = Path(f"data/exports/{filename}")
            self.file_manager.ensure_directory(output_path.parent)

            # Write CSV file
            self._write_csv_file(data, output_path)

            return output_path

        except Exception as e:
            raise ExportError(f"Failed to export CSV: {str(e)}")
    
    def _write_csv_file(self, data: List[Dict[str, Any]], output_path: Path):
        """Write data to CSV file with proper UTF-8 encoding.

        Args:
            data: List of data records
            output_path: Path to output CSV file
        """
        try:
            # Prepare data with proper encoding handling
            cleaned_data = []
            for record in data:
                cleaned_record = self._clean_record_data(record)
                cleaned_data.append(cleaned_record)

            # Use EncodingHelper for safe CSV writing
            EncodingHelper.write_csv_safely(
                data=cleaned_data,
                output_path=output_path,
                fieldnames=self.columns,
                include_headers=self.include_headers
            )

            self.log_debug(f"CSV written to {output_path}")

        except Exception as e:
            self.log_error(f"Failed to write CSV to {output_path}: {e}")
            raise
    
    def _clean_record_data(self, record: Dict[str, Any]) -> Dict[str, str]:
        """Clean and format record data for CSV export with proper encoding.

        Args:
            record: Raw data record

        Returns:
            Cleaned record data with proper UTF-8 encoding
        """
        cleaned = {}

        for column in self.columns:
            # Generate video_url dynamically from video_id
            if column == 'video_url':
                video_id = record.get('video_id', '')
                if video_id:
                    cleaned[column] = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    cleaned[column] = ''
                continue

            value = record.get(column, '')

            # Use EncodingHelper to clean and normalize the field
            cleaned[column] = EncodingHelper.clean_csv_field(value)

        return cleaned
    
    def export_tips_by_date_range(self, start_date: str, end_date: str = None) -> bool:
        """Export tips within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
            
        Returns:
            True if successful, False otherwise
        """
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        self.log_info(f"Exporting tips from {start_date} to {end_date}")

        try:
            # Validate dates
            self.validator.validate_date(start_date)
            if end_date:
                self.validator.validate_date(end_date)

            # Get tips within date range
            tips = self._get_tips_by_date_range(start_date, end_date)

            if not tips:
                self.log_warning(f"No tips found between {start_date} and {end_date}")
                return True

            # Generate filename with date range
            filename = f"tips_{start_date}_to_{end_date}.csv"

            # Export to CSV
            output_path = self._export_to_csv(tips, filename)

            self.log_info(f"Successfully exported {len(tips)} tips to {output_path}")
            return True

        except ValidationError as e:
            self.log_error(f"Invalid date format: {e}")
            return False
        except Exception as e:
            self.log_error(f"Failed to export tips by date range: {e}")
            return False
    
    def _get_tips_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get tips within a date range.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            List of tip records
        """
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT
                        v.id as video_id,
                        v.title as video_title,
                        v.published_at,
                        COALESCE(t.website, 'No tips found') as website,
                        COALESCE(t.use, 'Processing failed or no content found') as use,
                        COALESCE(t.details, CASE
                            WHEN v.status LIKE '%_error' THEN 'Error: ' || COALESCE(v.last_error, 'Unknown error')
                            WHEN v.status = 'new' THEN 'Not yet processed'
                            WHEN v.status = 'transcribed' THEN 'Transcript extracted, parsing pending'
                            WHEN v.status = 'parsed' THEN 'Parsed, vision analysis pending'
                            ELSE 'Processing status: ' || v.status
                        END) as details,
                        COALESCE(t.frame_path, '') as frame_path
                    FROM videos v
                    LEFT JOIN tips t ON t.video_id = v.id
                    WHERE v.published_at >= ? AND v.published_at <= ?
                    ORDER BY v.published_at DESC, t.website
                """, (start_date, end_date))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            self.log_error(f"Failed to get tips by date range: {e}")
            return []

    def export_summary_stats(self) -> bool:
        """Export summary statistics about the scraped data.

        Returns:
            True if successful, False otherwise
        """
        self.log_info("Exporting summary statistics")

        try:
            stats = self._generate_stats()

            # Generate filename
            filename = self._generate_filename(None, "summary_stats")

            # Ensure exports directory exists
            output_path = Path(f"data/exports/{filename}")
            self.file_manager.ensure_directory(output_path.parent)

            # Write stats to CSV using EncodingHelper
            stats_data = [
                {'Metric': metric, 'Value': value}
                for metric, value in stats.items()
            ]

            EncodingHelper.write_csv_safely(
                data=stats_data,
                output_path=output_path,
                fieldnames=['Metric', 'Value'],
                include_headers=True
            )

            self.log_info(f"Summary statistics exported to {output_path}")
            return True

        except Exception as e:
            self.log_error(f"Failed to export summary statistics: {e}")
            return False
    
    def _generate_stats(self) -> Dict[str, Any]:
        """Generate summary statistics.
        
        Returns:
            Dictionary of statistics
        """
        try:
            with self.db_manager.get_connection() as conn:
                stats = {}
                
                # Total videos
                cursor = conn.execute("SELECT COUNT(*) FROM videos")
                stats['Total Videos'] = cursor.fetchone()[0]
                
                # Videos by status
                cursor = conn.execute("""
                    SELECT status, COUNT(*) 
                    FROM videos 
                    GROUP BY status
                """)
                for row in cursor.fetchall():
                    stats[f'Videos - {row[0]}'] = row[1]
                
                # Total tips
                cursor = conn.execute("SELECT COUNT(*) FROM tips")
                stats['Total Tips'] = cursor.fetchone()[0]
                
                # Tips per video (average)
                cursor = conn.execute("""
                    SELECT AVG(tip_count) FROM (
                        SELECT COUNT(*) as tip_count 
                        FROM tips 
                        GROUP BY video_id
                    )
                """)
                avg_tips = cursor.fetchone()[0]
                stats['Average Tips per Video'] = round(avg_tips, 2) if avg_tips else 0
                
                # Most common websites
                cursor = conn.execute("""
                    SELECT website, COUNT(*) as count
                    FROM tips 
                    WHERE website != ''
                    GROUP BY website 
                    ORDER BY count DESC 
                    LIMIT 5
                """)
                top_websites = cursor.fetchall()
                for i, (website, count) in enumerate(top_websites, 1):
                    stats[f'Top Website #{i}'] = f"{website} ({count} mentions)"
                
                # Date range
                cursor = conn.execute("""
                    SELECT MIN(published_at), MAX(published_at) 
                    FROM videos
                """)
                date_range = cursor.fetchone()
                if date_range[0] and date_range[1]:
                    stats['Date Range'] = f"{date_range[0]} to {date_range[1]}"
                
                return stats

        except Exception as e:
            self.log_error(f"Failed to generate statistics: {e}")
            return {}

    def get_export_history(self) -> List[str]:
        """Get list of previously exported files.

        Returns:
            List of export filenames
        """
        try:
            exports_dir = Path("data/exports")
            if not exports_dir.exists():
                return []

            csv_files = list(exports_dir.glob("*.csv"))
            return [f.name for f in sorted(csv_files, key=lambda x: x.stat().st_mtime, reverse=True)]

        except Exception as e:
            self.log_error(f"Failed to get export history: {e}")
            return []
