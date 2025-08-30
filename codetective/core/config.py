"""
Configuration management for Codetective.
"""

from typing import Any

from pydantic import BaseModel, Field

from codetective.models.schemas import FixConfig, ScanConfig


class Config(BaseModel):
    """Global configuration for Codetective."""

    # Scan Config
    scan_config: ScanConfig = Field(default_factory=ScanConfig)

    # Fix Config
    fix_config: FixConfig = Field(default_factory=FixConfig)

    # Timeout settings
    agent_timeout: int = Field(default=900, description="Per-agent timeout in seconds")

    # Ollama configuration
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model: str = Field(default="qwen3:4b", description="Ollama model to use")

    # File handling
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum file size to scan (bytes)")
    backup_files: bool = Field(default=True, description="Create backup files before fixing")
    keep_backup: bool = Field(default=False, description="Keep backup files after fix completion")

    # GUI configuration
    gui_host: str = Field(default="localhost", description="GUI host")
    gui_port: int = Field(default=7891, description="GUI port")


def get_config(**kwargs: Any) -> Config:
    """Get the global configuration instance."""
    return Config(**kwargs)
