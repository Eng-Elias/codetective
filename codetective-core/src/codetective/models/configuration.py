"""
Configuration models for agents and system settings.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class AgentConfig:
    """Base agent configuration."""
    
    enabled: bool
    timeout: int
    retry_count: int
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if self.timeout <= 0:
            raise ValueError("timeout must be > 0")
        
        if self.retry_count < 0:
            raise ValueError("retry_count must be >= 0")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "custom_params": self.custom_params,
        }


@dataclass
class SemgrepConfig(AgentConfig):
    """Semgrep-specific configuration."""
    
    rules: List[str] = field(default_factory=list)  # Rule IDs or paths
    exclude_rules: List[str] = field(default_factory=list)
    config_path: str = ""
    severity_filter: List[str] = field(default_factory=lambda: ["ERROR", "WARNING"])
    
    def __post_init__(self) -> None:
        """Validate Semgrep configuration."""
        super().__post_init__()
        
        valid_severities = ["ERROR", "WARNING", "INFO"]
        for severity in self.severity_filter:
            if severity not in valid_severities:
                raise ValueError(f"Invalid severity filter: {severity}")
    
    def get_cli_args(self) -> List[str]:
        """Generate CLI arguments for Semgrep."""
        args = ["--json"]
        
        if self.config_path:
            args.extend(["--config", self.config_path])
        
        for rule in self.rules:
            args.extend(["--config", rule])
        
        for exclude_rule in self.exclude_rules:
            args.extend(["--exclude-rule", exclude_rule])
        
        if self.severity_filter:
            severity_str = ",".join(self.severity_filter)
            args.extend(["--severity", severity_str])
        
        return args
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            "rules": self.rules,
            "exclude_rules": self.exclude_rules,
            "config_path": self.config_path,
            "severity_filter": self.severity_filter,
        })
        return base_dict


@dataclass
class TrivyConfig(AgentConfig):
    """Trivy-specific configuration."""
    
    scan_types: List[str] = field(default_factory=lambda: ["vuln"])  # vuln, secret, config
    severity_filter: List[str] = field(default_factory=lambda: ["CRITICAL", "HIGH", "MEDIUM"])
    ignore_unfixed: bool = False
    
    def __post_init__(self) -> None:
        """Validate Trivy configuration."""
        super().__post_init__()
        
        valid_scan_types = ["vuln", "secret", "config", "license"]
        for scan_type in self.scan_types:
            if scan_type not in valid_scan_types:
                raise ValueError(f"Invalid scan type: {scan_type}")
        
        valid_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN"]
        for severity in self.severity_filter:
            if severity not in valid_severities:
                raise ValueError(f"Invalid severity filter: {severity}")
    
    def get_cli_args(self) -> List[str]:
        """Generate CLI arguments for Trivy."""
        args = ["--format", "json"]
        
        if self.scan_types:
            for scan_type in self.scan_types:
                args.extend(["--scanners", scan_type])
        
        if self.severity_filter:
            severity_str = ",".join(self.severity_filter)
            args.extend(["--severity", severity_str])
        
        if self.ignore_unfixed:
            args.append("--ignore-unfixed")
        
        return args
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            "scan_types": self.scan_types,
            "severity_filter": self.severity_filter,
            "ignore_unfixed": self.ignore_unfixed,
        })
        return base_dict


@dataclass
class AIReviewConfig(AgentConfig):
    """AI review agent configuration."""
    
    provider: str = "openai"  # openai, anthropic, gemini, ollama, lmstudio
    model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.1
    focus_areas: List[str] = field(default_factory=lambda: ["security", "performance", "maintainability"])
    
    def __post_init__(self) -> None:
        """Validate AI review configuration."""
        super().__post_init__()
        
        valid_providers = ["openai", "anthropic", "gemini", "ollama", "lmstudio"]
        if self.provider not in valid_providers:
            raise ValueError(f"Invalid provider: {self.provider}")
        
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be > 0")
        
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        
        valid_focus_areas = [
            "security", "performance", "maintainability", "readability", 
            "testing", "documentation", "architecture", "best_practices"
        ]
        for area in self.focus_areas:
            if area not in valid_focus_areas:
                raise ValueError(f"Invalid focus area: {area}")
    
    def get_model_params(self) -> Dict[str, Any]:
        """Get model parameters for API calls."""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        base_dict = super().to_dict()
        base_dict.update({
            "provider": self.provider,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "focus_areas": self.focus_areas,
        })
        return base_dict
