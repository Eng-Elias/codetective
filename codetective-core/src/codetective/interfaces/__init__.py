"""
Interface implementations for codetective.

This package contains the GUI, CLI, and MCP interface implementations
for the codetective multi-agent code review tool.
"""

from .gui import StreamlitGUI
from .cli import CodedetectiveCLI

__all__ = [
    "StreamlitGUI",
    "CodedetectiveCLI",
]
