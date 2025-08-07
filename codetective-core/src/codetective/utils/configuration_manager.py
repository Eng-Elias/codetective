"""
Configuration management utilities for the codetective system.
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import asdict

from loguru import logger

from codetective.models.configuration import (
    AgentConfig,
    SemgrepConfig,
    TrivyConfig,
    AIReviewConfig,
)
from codetective.utils.logger import LogLevel


class ConfigurationManager:
    """
    Manages configuration loading, validation, and persistence.
    
    This class handles configuration files, environment variables,
    and provides a unified interface for accessing system settings.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self._config_data: Dict[str, Any] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        
        # Load configuration from various sources
        self._load_default_config()
        if config_path and config_path.exists():
            self._load_config_file(config_path)
        self._load_environment_variables()
        
        # Initialize agent configurations
        self._initialize_agent_configs()
    
    @property
    def config_data(self) -> Dict[str, Any]:
        """Get the current configuration data."""
        return self._config_data.copy()
    
    @property
    def agent_configs(self) -> Dict[str, AgentConfig]:
        """Get agent configurations."""
        return self._agent_configs.copy()
    
    def _load_default_config(self) -> None:
        """Load default configuration values."""
        self._config_data = {
            "general": {
                "log_level": LogLevel.INFO,
                "max_file_size": 1024 * 1024,  # 1MB
                "timeout": 300,  # 5 minutes
                "parallel_execution": True,
            },
            "agents": {
                "semgrep": {
                    "enabled": True,
                    "timeout": 120,
                    "retry_count": 2,
                    "rules": [],
                    "exclude_rules": [],
                    "config_path": "",
                    "severity_filter": ["ERROR", "WARNING"],
                },
                "trivy": {
                    "enabled": True,
                    "timeout": 180,
                    "retry_count": 2,
                    "scan_types": ["vuln"],
                    "severity_filter": ["CRITICAL", "HIGH", "MEDIUM"],
                    "ignore_unfixed": False,
                },
                "ai_review": {
                    "enabled": True,
                    "timeout": 300,
                    "retry_count": 1,
                    "provider": "openai",
                    "model": "gpt-4",
                    "max_tokens": 4000,
                    "temperature": 0.1,
                    "focus_areas": ["security", "performance", "maintainability"],
                },
            },
            "interfaces": {
                "gui": {
                    "port": 8501,
                    "host": "localhost",
                    "theme": "light",
                },
                "cli": {
                    "default_output_format": "json",
                    "verbose": False,
                },
                "mcp": {
                    "port": 8502,
                    "host": "localhost",
                },
            },
            "security": {
                "api_key_env_vars": {
                    "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                    "gemini": "GEMINI_API_KEY",
                },
                "backup_before_changes": True,
                "validate_inputs": True,
            },
        }
    
    def _load_config_file(self, config_path: Path) -> None:
        """
        Load configuration from a file.
        
        Args:
            config_path: Path to the configuration file
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    file_config = yaml.safe_load(f)
                elif config_path.suffix.lower() == '.json':
                    file_config = json.load(f)
                else:
                    logger.warning(f"Unsupported config file format: {config_path.suffix}")
                    return
            
            # Merge file config with default config
            self._merge_config(self._config_data, file_config)
            logger.info(f"Loaded configuration from {config_path}")
        
        except Exception as e:
            logger.error(f"Error loading config file {config_path}: {e}")
            raise
    
    def _load_environment_variables(self) -> None:
        """Load configuration from environment variables."""
        # General settings
        if log_level := os.getenv("CODETECTIVE_LOG_LEVEL"):
            self._config_data["general"]["log_level"] = log_level
        
        if timeout := os.getenv("CODETECTIVE_TIMEOUT"):
            try:
                self._config_data["general"]["timeout"] = int(timeout)
            except ValueError:
                logger.warning(f"Invalid timeout value in environment: {timeout}")
        
        # Agent settings
        for agent_name in ["semgrep", "trivy", "ai_review"]:
            env_prefix = f"CODETECTIVE_{agent_name.upper()}"
            
            if enabled := os.getenv(f"{env_prefix}_ENABLED"):
                self._config_data["agents"][agent_name]["enabled"] = enabled.lower() == "true"
            
            if timeout := os.getenv(f"{env_prefix}_TIMEOUT"):
                try:
                    self._config_data["agents"][agent_name]["timeout"] = int(timeout)
                except ValueError:
                    logger.warning(f"Invalid timeout for {agent_name}: {timeout}")
        
        # AI Review specific settings
        if provider := os.getenv("CODETECTIVE_AI_PROVIDER"):
            self._config_data["agents"]["ai_review"]["provider"] = provider
        
        if model := os.getenv("CODETECTIVE_AI_MODEL"):
            self._config_data["agents"]["ai_review"]["model"] = model
        
        logger.debug("Loaded configuration from environment variables")
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        Recursively merge configuration dictionaries.
        
        Args:
            base: Base configuration dictionary
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value
    
    def _initialize_agent_configs(self) -> None:
        """Initialize typed agent configuration objects."""
        try:
            # Semgrep configuration
            semgrep_data = self._config_data["agents"]["semgrep"]
            self._agent_configs["semgrep"] = SemgrepConfig(
                enabled=semgrep_data["enabled"],
                timeout=semgrep_data["timeout"],
                retry_count=semgrep_data["retry_count"],
                rules=semgrep_data["rules"],
                exclude_rules=semgrep_data["exclude_rules"],
                config_path=semgrep_data["config_path"],
                severity_filter=semgrep_data["severity_filter"],
            )
            
            # Trivy configuration
            trivy_data = self._config_data["agents"]["trivy"]
            self._agent_configs["trivy"] = TrivyConfig(
                enabled=trivy_data["enabled"],
                timeout=trivy_data["timeout"],
                retry_count=trivy_data["retry_count"],
                scan_types=trivy_data["scan_types"],
                severity_filter=trivy_data["severity_filter"],
                ignore_unfixed=trivy_data["ignore_unfixed"],
            )
            
            # AI Review configuration
            ai_data = self._config_data["agents"]["ai_review"]
            self._agent_configs["ai_review"] = AIReviewConfig(
                enabled=ai_data["enabled"],
                timeout=ai_data["timeout"],
                retry_count=ai_data["retry_count"],
                provider=ai_data["provider"],
                model=ai_data["model"],
                max_tokens=ai_data["max_tokens"],
                temperature=ai_data["temperature"],
                focus_areas=ai_data["focus_areas"],
            )
            
            logger.debug("Initialized agent configurations")
        
        except Exception as e:
            logger.error(f"Error initializing agent configs: {e}")
            raise
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """
        Get configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration object or None if not found
        """
        return self._agent_configs.get(agent_name)
    
    def update_agent_config(self, agent_name: str, config: AgentConfig) -> None:
        """
        Update configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            config: New configuration object
        """
        self._agent_configs[agent_name] = config
        
        # Update the underlying config data
        if agent_name in self._config_data["agents"]:
            self._config_data["agents"][agent_name].update(asdict(config))
        
        logger.info(f"Updated configuration for agent: {agent_name}")
    
    def get_setting(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration setting using dot notation.
        
        Args:
            key_path: Dot-separated path to the setting (e.g., "general.timeout")
            default: Default value if setting not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split(".")
        current = self._config_data
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set_setting(self, key_path: str, value: Any) -> None:
        """
        Set a configuration setting using dot notation.
        
        Args:
            key_path: Dot-separated path to the setting
            value: Value to set
        """
        keys = key_path.split(".")
        current = self._config_data
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        logger.debug(f"Set configuration: {key_path} = {value}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Provider name (e.g., "openai", "anthropic")
            
        Returns:
            API key or None if not found
        """
        env_var = self._config_data["security"]["api_key_env_vars"].get(provider)
        if env_var:
            return os.getenv(env_var)
        return None
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Validate general settings
        if self._config_data["general"]["timeout"] <= 0:
            errors.append("General timeout must be > 0")
        
        # Validate agent configurations
        for agent_name, config in self._agent_configs.items():
            try:
                # This will raise ValueError if config is invalid
                config.__post_init__()
            except ValueError as e:
                errors.append(f"Invalid {agent_name} config: {e}")
        
        # Validate API keys for enabled AI agents
        if self._agent_configs.get("ai_review", AgentConfig(False, 0, 0)).enabled:
            ai_config = self._agent_configs["ai_review"]
            if isinstance(ai_config, AIReviewConfig):
                api_key = self.get_api_key(ai_config.provider)
                if not api_key:
                    errors.append(f"Missing API key for {ai_config.provider}")
        
        return errors
    
    def save_config(self, output_path: Path, format: str = "yaml") -> None:
        """
        Save current configuration to a file.
        
        Args:
            output_path: Path to save the configuration
            format: Output format ("yaml" or "json")
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if format.lower() == "yaml":
                    yaml.dump(self._config_data, f, default_flow_style=False, indent=2)
                elif format.lower() == "json":
                    json.dump(self._config_data, f, indent=2)
                else:
                    raise ValueError(f"Unsupported format: {format}")
            
            logger.info(f"Saved configuration to {output_path}")
        
        except Exception as e:
            logger.error(f"Error saving config to {output_path}: {e}")
            raise
    
    def get_enabled_agents(self) -> List[str]:
        """Get list of enabled agent names."""
        return [
            name for name, config in self._agent_configs.items()
            if config.enabled
        ]
    
    def is_agent_enabled(self, agent_name: str) -> bool:
        """Check if a specific agent is enabled."""
        config = self._agent_configs.get(agent_name)
        return config.enabled if config else False
    
    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "enabled_agents": self.get_enabled_agents(),
            "general_settings": self._config_data["general"],
            "interface_settings": self._config_data["interfaces"],
            "validation_errors": self.validate_configuration(),
            "config_source": str(self.config_path) if self.config_path else "default",
        }
