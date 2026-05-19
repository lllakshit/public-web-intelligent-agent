from __future__ import annotations

from urllib.parse import urlparse

import requests
import trafilatura
from bs4 import BeautifulSoup

from public_web_agent.search import USER_AGENT


FETCH_BLOCKED_DOMAINS = {
    "linkedin.com",
    "facebook.com",
    "instagram.com",
    "x.com",
    "twitter.com",
}


def is_fetch_allowed(url: str) -> tuple[bool, str]:
    domain = urlparse(url).netloc.lower().removeprefix("www.")
    if any(domain == blocked or domain.endswith(f".{blocked}") for blocked in FETCH_BLOCKED_DOMAINS):
        return False, "listed from search results only; page is commonly login-gated or restricted"
    return True, ""


def extract_public_page(url: str, max_chars: int = 12000) -> tuple[str, str]:
    allowed, reason = is_fetch_allowed(url)
    if not allowed:
        return "", reason

    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    if "pdf" in content_type:
        return "", "PDF extraction is not enabled in this web-first collector"
    if "text/html" not in content_type and "application/xhtml" not in content_type:
        return "", f"unsupported content type: {content_type or 'unknown'}"

    extracted = trafilatura.extract(response.text, url=url, include_comments=False, include_tables=False) or ""
    if not extracted.strip():
        soup = BeautifulSoup(response.text, "html.parser")
        for node in soup(["script", "style", "noscript", "svg"]):
            node.decompose()
        extracted = " ".join(p.get_text(" ", strip=True) for p in soup.find_all(["p", "li", "h1", "h2", "h3"]))

    text = " ".join(extracted.split())
    if not text:
        return "", "no readable public text found"
    return text[:max_chars], "fetched"

