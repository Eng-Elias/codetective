"""
Agent system for Codetective.
"""

from .base import BaseAgent
from .scan.semgrep_agent import SemGrepAgent
from .scan.trivy_agent import TrivyAgent
from .scan.ai_review_agent import AIReviewAgent
from .output.comment_agent import CommentAgent
from .output.edit_agent import EditAgent

__all__ = [
    "BaseAgent",
    "SemGrepAgent", 
    "TrivyAgent",
    "AIReviewAgent",
    "CommentAgent",
    "EditAgent"
]
