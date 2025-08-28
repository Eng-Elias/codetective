"""
Agent system for Codetective.
"""

from .base import BaseAgent
from .output.comment_agent import CommentAgent
from .output.edit_agent import EditAgent
from .scan.dynamic_ai_review_agent import DynamicAIReviewAgent
from .scan.semgrep_agent import SemGrepAgent
from .scan.trivy_agent import TrivyAgent

__all__ = ["BaseAgent", "SemGrepAgent", "TrivyAgent", "DynamicAIReviewAgent", "CommentAgent", "EditAgent"]
