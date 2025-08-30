"""
String utilities for Codetective - handle text formatting and JSON operations.
"""

import json
from datetime import datetime
from typing import Any


class StringUtils:
    """Utility class for string-related operations."""

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable string."""
        if seconds < 1:
            return f"{seconds:.2f}s"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            return f"{hours}h {remaining_minutes}m"

    @staticmethod
    def truncate_text(text: str, max_length: int = 100) -> str:
        """Truncate text to maximum length with ellipsis."""
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."

    @staticmethod
    def safe_json_dump(data: Any) -> str:
        """Safely dump data to JSON string with error handling."""

        def json_serializer(obj: Any) -> str:
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, "model_dump"):
                return str(obj.model_dump())
            elif hasattr(obj, "__dict__"):
                return str(obj.__dict__)
            return str(obj)

        try:
            return json.dumps(data, indent=2, default=json_serializer)
        except Exception as e:
            return f'{{"error": "Failed to serialize data: {e}"}}'
