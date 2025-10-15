"""
Unit tests for StringUtils.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import Mock

from codetective.utils.string_utils import StringUtils


class TestStringUtils:
    """Test cases for StringUtils."""

    @pytest.mark.unit
    def test_format_duration_less_than_one_second(self):
        """Test formatting duration less than 1 second."""
        result = StringUtils.format_duration(0.5)
        assert result == "0.50s"
        
        result = StringUtils.format_duration(0.123)
        assert result == "0.12s"

    @pytest.mark.unit
    def test_format_duration_seconds(self):
        """Test formatting duration in seconds."""
        result = StringUtils.format_duration(5.5)
        assert result == "5.5s"
        
        result = StringUtils.format_duration(45.7)
        assert result == "45.7s"

    @pytest.mark.unit
    def test_format_duration_minutes(self):
        """Test formatting duration in minutes."""
        result = StringUtils.format_duration(90.0)  # 1 minute 30 seconds
        assert "1m" in result
        assert "30" in result
        
        result = StringUtils.format_duration(125.5)  # 2 minutes 5.5 seconds
        assert "2m" in result
        assert "5.5s" in result

    @pytest.mark.unit
    def test_format_duration_hours(self):
        """Test formatting duration in hours."""
        result = StringUtils.format_duration(3600.0)  # 1 hour
        assert "1h" in result
        assert "0m" in result
        
        result = StringUtils.format_duration(3750.0)  # 1 hour 2 minutes 30 seconds
        assert "1h" in result
        assert "2m" in result

    @pytest.mark.unit
    def test_format_duration_edge_cases(self):
        """Test formatting duration edge cases."""
        # Zero
        result = StringUtils.format_duration(0.0)
        assert result == "0.00s"
        
        # Exactly 60 seconds
        result = StringUtils.format_duration(60.0)
        assert "1m" in result
        
        # Exactly 3600 seconds
        result = StringUtils.format_duration(3600.0)
        assert "1h" in result

    @pytest.mark.unit
    def test_truncate_text_short_text(self):
        """Test truncating text shorter than max length."""
        text = "Short text"
        result = StringUtils.truncate_text(text, max_length=100)
        assert result == text
        
        result = StringUtils.truncate_text(text, max_length=20)
        assert result == text

    @pytest.mark.unit
    def test_truncate_text_long_text(self):
        """Test truncating text longer than max length."""
        text = "This is a very long text that needs to be truncated"
        result = StringUtils.truncate_text(text, max_length=20)
        
        assert len(result) == 20
        assert result.endswith("...")
        assert result.startswith("This is a very")

    @pytest.mark.unit
    def test_truncate_text_default_length(self):
        """Test truncating with default max length."""
        text = "a" * 150  # 150 characters
        result = StringUtils.truncate_text(text)
        
        assert len(result) == 100  # Default max length
        assert result.endswith("...")

    @pytest.mark.unit
    def test_truncate_text_exactly_max_length(self):
        """Test truncating text exactly at max length."""
        text = "a" * 20
        result = StringUtils.truncate_text(text, max_length=20)
        
        # Should not truncate
        assert result == text
        assert not result.endswith("...")

    @pytest.mark.unit
    def test_truncate_text_empty_string(self):
        """Test truncating empty string."""
        result = StringUtils.truncate_text("", max_length=10)
        assert result == ""

    @pytest.mark.unit
    def test_safe_json_dump_simple_data(self):
        """Test safe JSON dump with simple data."""
        data = {"name": "test", "value": 123}
        result = StringUtils.safe_json_dump(data)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["name"] == "test"
        assert parsed["value"] == 123

    @pytest.mark.unit
    def test_safe_json_dump_nested_data(self):
        """Test safe JSON dump with nested data."""
        data = {
            "level1": {
                "level2": {
                    "level3": "deep value"
                }
            },
            "list": [1, 2, 3]
        }
        result = StringUtils.safe_json_dump(data)
        
        parsed = json.loads(result)
        assert parsed["level1"]["level2"]["level3"] == "deep value"
        assert parsed["list"] == [1, 2, 3]

    @pytest.mark.unit
    def test_safe_json_dump_with_datetime(self):
        """Test safe JSON dump with datetime objects."""
        now = datetime(2024, 1, 1, 12, 0, 0)
        data = {"timestamp": now}
        
        result = StringUtils.safe_json_dump(data)
        
        # Should serialize datetime to ISO format
        parsed = json.loads(result)
        assert "2024-01-01" in parsed["timestamp"]

    @pytest.mark.unit
    def test_safe_json_dump_with_model_dump(self):
        """Test safe JSON dump with objects that have model_dump."""
        # Create mock object with model_dump method
        mock_obj = Mock()
        mock_obj.model_dump.return_value = {"field": "value"}
        
        data = {"model": mock_obj}
        result = StringUtils.safe_json_dump(data)
        
        # Should call model_dump and serialize
        assert "field" in result or "value" in result

    @pytest.mark.unit
    def test_safe_json_dump_with_dict_attr(self):
        """Test safe JSON dump with objects that have __dict__."""
        class CustomObject:
            def __init__(self):
                self.name = "test"
                self.value = 42
        
        obj = CustomObject()
        data = {"object": obj}
        
        result = StringUtils.safe_json_dump(data)
        
        # Should serialize using __dict__
        assert "name" in result or "test" in result

    @pytest.mark.unit
    def test_safe_json_dump_with_non_serializable(self):
        """Test safe JSON dump with non-serializable objects."""
        # Lambda functions are not serializable
        data = {"function": lambda x: x}
        
        result = StringUtils.safe_json_dump(data)
        
        # Should convert to string representation
        assert isinstance(result, str)
        assert "lambda" in result or "function" in result

    @pytest.mark.unit
    def test_safe_json_dump_handles_circular_reference(self):
        """Test safe JSON dump handles circular references gracefully."""
        data = {"key": "value"}
        data["self"] = data  # Circular reference
        
        result = StringUtils.safe_json_dump(data)
        
        # Should return error message instead of crashing
        assert isinstance(result, str)
        # May contain error message due to circular reference

    @pytest.mark.unit
    def test_safe_json_dump_empty_dict(self):
        """Test safe JSON dump with empty dictionary."""
        result = StringUtils.safe_json_dump({})
        
        parsed = json.loads(result)
        assert parsed == {}

    @pytest.mark.unit
    def test_safe_json_dump_empty_list(self):
        """Test safe JSON dump with empty list."""
        result = StringUtils.safe_json_dump([])
        
        parsed = json.loads(result)
        assert parsed == []

    @pytest.mark.unit
    def test_safe_json_dump_with_none(self):
        """Test safe JSON dump with None value."""
        data = {"value": None}
        result = StringUtils.safe_json_dump(data)
        
        parsed = json.loads(result)
        assert parsed["value"] is None

    @pytest.mark.unit
    def test_safe_json_dump_with_boolean(self):
        """Test safe JSON dump with boolean values."""
        data = {"true_val": True, "false_val": False}
        result = StringUtils.safe_json_dump(data)
        
        parsed = json.loads(result)
        assert parsed["true_val"] is True
        assert parsed["false_val"] is False

    @pytest.mark.unit
    def test_safe_json_dump_with_numbers(self):
        """Test safe JSON dump with various number types."""
        data = {
            "int": 42,
            "float": 3.14,
            "negative": -10,
            "zero": 0
        }
        result = StringUtils.safe_json_dump(data)
        
        parsed = json.loads(result)
        assert parsed["int"] == 42
        assert parsed["float"] == 3.14
        assert parsed["negative"] == -10
        assert parsed["zero"] == 0

    @pytest.mark.unit
    def test_safe_json_dump_formatted_output(self):
        """Test safe JSON dump produces formatted output."""
        data = {"key1": "value1", "key2": "value2"}
        result = StringUtils.safe_json_dump(data)
        
        # Should have indentation (formatted)
        assert "\n" in result
        assert "  " in result  # 2-space indentation
