"""
Search utilities for Codetective AI agents.
"""

import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS

logger = logging.getLogger(__name__)


class SearchType(Enum):
    TEXT = "text"
    NEWS = "news"
    IMAGES = "images"


class SearchTool:
    """DuckDuckGo search tool for AI agents with URL content fetching."""

    def __init__(self, max_results: int = 5):
        """Initialize search tool.

        Args:
            max_results: Maximum number of search results to return
        """
        self.max_results = max_results
        self.ddgs = DDGS()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})

    def search(self, query: str, search_type: SearchType = SearchType.TEXT) -> List[Dict[str, Any]]:
        """Perform a search query.

        Args:
            query: Search query string
            search_type: Type of search (SearchType.TEXT, SearchType.NEWS, SearchType.IMAGES)

        Returns:
            List of search results with title, body, and href
        """
        try:
            if search_type == SearchType.TEXT:
                results = list(self.ddgs.text(query, max_results=self.max_results))
            elif search_type == SearchType.NEWS:
                results = list(self.ddgs.news(query, max_results=self.max_results))
            else:
                results = list(self.ddgs.text(query, max_results=self.max_results))

            # Format results for AI consumption
            formatted_results = []
            for result in results:
                formatted_results.append(
                    {
                        "title": result.get("title", ""),
                        "body": result.get("body", ""),
                        "url": result.get("href", ""),
                        "source": "DuckDuckGo",
                    }
                )

            return formatted_results

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def search_code_patterns(self, language: str, pattern: str) -> List[Dict[str, Any]]:
        """Search for code patterns and best practices.

        Args:
            language: Programming language
            pattern: Code pattern or issue to search for

        Returns:
            List of relevant search results
        """
        query = f"{language} {pattern} best practices security vulnerability fix"
        return self.search(query)

    def search_security_info(
        self, cve_id: Optional[str] = None, vulnerability_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for security vulnerability information.

        Args:
            cve_id: CVE identifier if available
            vulnerability_type: Type of vulnerability

        Returns:
            List of security-related search results
        """
        if cve_id:
            query = f"CVE {cve_id} vulnerability details fix"
        elif vulnerability_type:
            query = f"{vulnerability_type} security vulnerability fix mitigation"
        else:
            query = "security vulnerability best practices"

        return self.search(query)

    def search_documentation(self, library: str, function: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for library/framework documentation.

        Args:
            library: Library or framework name
            function: Specific function or method

        Returns:
            List of documentation search results
        """
        if function:
            query = f"{library} {function} documentation examples"
        else:
            query = f"{library} documentation official guide"

        return self.search(query)

    def fetch_url_content(self, url: str, max_length: int = 10000) -> Optional[str]:
        """Fetch and extract text content from a URL.

        Args:
            url: URL to fetch content from
            max_length: Maximum length of content to return

        Returns:
            Extracted text content or None if failed
        """
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Parse HTML content
            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract text
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)

            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."

            return text

        except Exception as e:
            logger.error(f"Failed to fetch URL content from {url}: {e}")
            return None

    def search_with_content(self, query: str, fetch_content: bool = True) -> List[Dict[str, Any]]:
        """Search and optionally fetch full content from URLs.

        Args:
            query: Search query
            fetch_content: Whether to fetch full content from URLs

        Returns:
            Search results with optional full content
        """
        results = self.search(query)

        if not fetch_content:
            return results

        enhanced_results = []
        for result in results:
            enhanced_result = result.copy()

            # Fetch full content if URL is available
            if result.get("url"):
                content = self.fetch_url_content(result["url"])
                if content:
                    enhanced_result["full_content"] = content
                    enhanced_result["has_full_content"] = True
                else:
                    enhanced_result["has_full_content"] = False

            enhanced_results.append(enhanced_result)

            # Add small delay to be respectful to servers
            time.sleep(0.5)

        return enhanced_results
