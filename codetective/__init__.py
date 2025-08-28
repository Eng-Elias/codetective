"""
Codetective - Multi-Agent Code Review Tool

A comprehensive code analysis tool that combines multiple scanning engines
(SemGrep, Trivy, AI) with automated fixing capabilities.
"""

__version__ = "0.1.0"
__author__ = "Codetective Team"
__description__ = "Multi-Agent Code Review Tool"

from .core.config import Config
from .models.schemas import AgentResult, ScanResult

__all__ = ["Config", "ScanResult", "AgentResult"]
