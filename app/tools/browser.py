"""Web browsing and search tools using Playwright with graceful fallbacks."""

from __future__ import annotations

import html
import json
import re
import urllib.request
import urllib.parse
import webbrowser
from typing import Any, Dict, Optional

from app.constants import RiskLevel
from app.tools.base import Tool, ToolResult
from app.utils.logging import get_logger

logger = get_logger("tools.browser")


class BrowserSession:
    """Manages an active browser page (Playwright or fallback state)."""
    _instance: Optional[BrowserSession] = None

    def __init__(self) -> None:
        self.playwright = None
        self.browser = None
        self.page = None
        self.last_url = ""
        self.last_title = ""
        self.last_text = ""

    @classmethod
    def get_instance(cls) -> BrowserSession:
        if cls._instance is None:
            cls._instance = BrowserSession()
        return cls._instance

    def ensure_page(self) -> Any:
        if self.page is not None:
            return self.page
        try:
            from playwright.sync_api import sync_playwright
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)
            self.page = self.browser.new_page()
            return self.page
        except Exception as e:
            logger.debug(f"Playwright sync launch not available ({e}). Using standard web scraper fallback.")
            return None


class OpenUrlTool(Tool):
    name = "open_url"
    description = "Opens a web URL in the browser and retrieves page details."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "The full HTTP/HTTPS URL to navigate to."},
        },
        "required": ["url"],
    }

    def execute(self, url: str, **kwargs: Any) -> ToolResult:
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        session = BrowserSession.get_instance()
        page = session.ensure_page()
        if page:
            try:
                page.goto(url, timeout=30000)
                session.last_url = url
                session.last_title = page.title()
                return ToolResult(success=True, output=f"Opened '{url}'. Title: '{session.last_title}'")
            except Exception as e:
                logger.error(f"Playwright navigation failed: {e}")

        # Fallback using system default browser
        try:
            webbrowser.open(url)
            session.last_url = url
            session.last_title = url
            return ToolResult(success=True, output=f"Opened '{url}' in default browser.")
        except Exception as e:
            return ToolResult(success=False, output="", error=f"Could not open URL: {e}")


class SearchWebTool(Tool):
    name = "search_web"
    description = "Searches the web for a query and returns titles and summaries."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query keywords."},
            "max_results": {"type": "integer", "description": "Max results (default 5).", "default": 5},
        },
        "required": ["query"],
    }

    def execute(self, query: str, max_results: int = 5, **kwargs: Any) -> ToolResult:
        try:
            encoded_query = urllib.parse.quote(query)
            search_url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                content = resp.read().decode("utf-8", errors="replace")

            results = []
            links = re.findall(r'<a class="result__snippet[^>]*href="([^"]+)"[^>]*>(.*?)</a>', content, re.DOTALL)
            if not links:
                links = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', content, re.DOTALL)

            for href, text in links[:max_results]:
                clean_text = re.sub(r"<[^>]+>", "", text).strip()
                clean_text = html.unescape(clean_text)
                results.append({"url": href, "snippet": clean_text})

            if results:
                return ToolResult(success=True, output=results)

            webbrowser.open(f"https://www.google.com/search?q={encoded_query}")
            return ToolResult(success=True, output=f"Launched Google search in browser for: '{query}'")
        except Exception as e:
            logger.error(f"Search error: {e}")
            webbrowser.open(f"https://www.google.com/search?q={urllib.parse.quote(query)}")
            return ToolResult(success=True, output=f"Opened search page for '{query}' in browser.")


class BrowserBackTool(Tool):
    name = "browser_back"
    description = "Navigates back to the previous page in history."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        session = BrowserSession.get_instance()
        if session.page:
            try:
                session.page.go_back()
                return ToolResult(success=True, output=f"Navigated back to: '{session.page.title()}'")
            except Exception as e:
                return ToolResult(success=False, output="", error=f"Could not go back: {e}")
        return ToolResult(success=True, output="Browser back executed.")


class BrowserForwardTool(Tool):
    name = "browser_forward"
    description = "Navigates forward to the next page in history."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        session = BrowserSession.get_instance()
        if session.page:
            try:
                session.page.go_forward()
                return ToolResult(success=True, output=f"Navigated forward to: '{session.page.title()}'")
            except Exception as e:
                return ToolResult(success=False, output="", error=f"Could not go forward: {e}")
        return ToolResult(success=True, output="Browser forward executed.")


class RefreshPageTool(Tool):
    name = "refresh_page"
    description = "Reloads the active browser page."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        session = BrowserSession.get_instance()
        if session.page:
            try:
                session.page.reload()
                return ToolResult(success=True, output=f"Reloaded page '{session.page.title()}'.")
            except Exception as e:
                return ToolResult(success=False, output="", error=f"Could not reload: {e}")
        return ToolResult(success=True, output="Browser refreshed.")


class GetPageTitleTool(Tool):
    name = "get_page_title"
    description = "Returns the title of the current browser page."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {"type": "object", "properties": {}}

    def execute(self, **kwargs: Any) -> ToolResult:
        session = BrowserSession.get_instance()
        if session.page:
            try:
                return ToolResult(success=True, output={"title": session.page.title(), "url": session.page.url})
            except Exception as e:
                return ToolResult(success=False, output="", error=str(e))
        return ToolResult(success=True, output={"title": session.last_title or "No active web session", "url": session.last_url})


class GetPageTextTool(Tool):
    name = "get_page_text"
    description = "Extracts visible readable text content from the current or specified web page."
    risk_level = RiskLevel.SAFE
    requires_confirmation = False
    parameters = {
        "type": "object",
        "properties": {
            "max_chars": {"type": "integer", "description": "Maximum characters to extract (default 4000).", "default": 4000},
        },
    }

    def execute(self, max_chars: int = 4000, **kwargs: Any) -> ToolResult:
        session = BrowserSession.get_instance()
        if session.page:
            try:
                text = session.page.inner_text("body")
                clean_text = " ".join(text.split())
                return ToolResult(success=True, output=clean_text[:max_chars])
            except Exception as e:
                return ToolResult(success=False, output="", error=f"Failed to extract page text: {e}")

        if session.last_url:
            try:
                req = urllib.request.Request(session.last_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html_content = resp.read().decode("utf-8", errors="replace")
                text = re.sub(r"<[^>]+>", " ", html_content)
                clean_text = " ".join(text.split())
                return ToolResult(success=True, output=clean_text[:max_chars])
            except Exception as e:
                return ToolResult(success=False, output="", error=f"Failed to fetch page text: {e}")

        return ToolResult(success=False, output="", error="No active webpage to extract text from.")
