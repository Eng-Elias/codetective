"""
Configuration management for Codetective.
"""

import os
import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Global configuration for Codetective."""
    
    # Agent configuration
    semgrep_enabled: bool = Field(default=True, description="Enable SemGrep agent")
    trivy_enabled: bool = Field(default=True, description="Enable Trivy agent")
    ai_review_enabled: bool = Field(default=True, description="Enable AI review agent")
    
    # Timeout settings
    default_timeout: int = Field(default=300, description="Default timeout in seconds")
    agent_timeout: int = Field(default=120, description="Per-agent timeout in seconds")
    
    # Ollama configuration
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model: str = Field(default="codellama", description="Ollama model to use")
    
    # File handling
    max_file_size: int = Field(default=10 * 1024 * 1024, description="Maximum file size to scan (bytes)")
    backup_files: bool = Field(default=True, description="Create backup files before fixing")
    
    # Output configuration
    output_format: str = Field(default="json", description="Default output format")
    verbose: bool = Field(default=False, description="Enable verbose output")
    
    # GUI configuration
    gui_host: str = Field(default="localhost", description="GUI host")
    gui_port: int = Field(default=7891, description="GUI port")
    
    @classmethod
    def load_from_file(cls, config_path: Optional[str] = None) -> "Config":
        """Load configuration from file."""
        if config_path is None:
            # Try default locations
            config_paths = [
                Path.cwd() / ".codetective.yaml",
                Path.home() / ".codetective" / "config.yaml",
                Path.home() / ".codetective.yaml"
            ]
            
            for path in config_paths:
                if path.exists():
                    config_path = str(path)
                    break
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return cls(**config_data)
        
        return cls()
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        env_config = {}
        
        # Map environment variables to config fields
        env_mapping = {
            "CODETECTIVE_SEMGREP_ENABLED": "semgrep_enabled",
            "CODETECTIVE_TRIVY_ENABLED": "trivy_enabled",
            "CODETECTIVE_AI_REVIEW_ENABLED": "ai_review_enabled",
            "CODETECTIVE_DEFAULT_TIMEOUT": "default_timeout",
            "CODETECTIVE_AGENT_TIMEOUT": "agent_timeout",
            "CODETECTIVE_OLLAMA_BASE_URL": "ollama_base_url",
            "CODETECTIVE_OLLAMA_MODEL": "ollama_model",
            "CODETECTIVE_MAX_FILE_SIZE": "max_file_size",
            "CODETECTIVE_BACKUP_FILES": "backup_files",
            "CODETECTIVE_OUTPUT_FORMAT": "output_format",
            "CODETECTIVE_VERBOSE": "verbose",
            "CODETECTIVE_GUI_HOST": "gui_host",
            "CODETECTIVE_GUI_PORT": "gui_port",
            "CODETECTIVE_GUI_TYPE": "gui_type",
        }
        
        for env_var, config_field in env_mapping.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_field in ["semgrep_enabled", "trivy_enabled", "ai_review_enabled", "backup_files", "verbose"]:
                    env_config[config_field] = value.lower() in ("true", "1", "yes", "on")
                elif config_field in ["default_timeout", "agent_timeout", "max_file_size", "gui_port"]:
                    env_config[config_field] = int(value)
                else:
                    env_config[config_field] = value
        
        return cls(**env_config)
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to file."""
        config_dir = Path(config_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
    
    def merge_with_cli_args(self, **kwargs) -> "Config":
        """Merge configuration with CLI arguments."""
        config_dict = self.model_dump()
        
        # Update with non-None CLI arguments
        for key, value in kwargs.items():
            if value is not None:
                config_dict[key] = value
        
        return Config(**config_dict)


def get_config() -> Config:
    """Get the global configuration instance."""
    # Priority: Environment variables > Config file > Defaults
    file_config = Config.load_from_file()
    env_config = Config.from_env()
    
    # Merge configurations (env takes precedence)
    merged_config = file_config.model_dump()
    merged_config.update({k: v for k, v in env_config.model_dump().items() 
                         if v != Config().model_dump()[k]})
    
    return Config(**merged_config)
