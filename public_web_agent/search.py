from __future__ import annotations

import re
from html import unescape
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from xml.etree import ElementTree

import requests
from bs4 import BeautifulSoup

from public_web_agent.models import SearchResult


DUCKDUCKGO_HTML_URL = "https://html.duckduckgo.com/html/"
BING_SEARCH_URL = "https://www.bing.com/search"
GOOGLE_NEWS_RSS_URL = "https://news.google.com/rss/search"
HACKER_NEWS_SEARCH_URL = "https://hn.algolia.com/api/v1/search"
REDDIT_SEARCH_URL = "https://www.reddit.com/search.json"
USER_AGENT = "Mozilla/5.0 (compatible; PublicWebIntelligenceAgent/1.0; +https://github.com/lllakshit/public-web-intelligent-agent)"
SEARCH_STOPWORDS = {
    "about", "after", "from", "latest", "search", "site", "with", "updates", "find", "this",
    "that", "what", "where", "when", "roles", "jobs", "public", "official", "discussion",
}


def normalize_ddg_url(url: str) -> str:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    if "uddg" in query and query["uddg"]:
        return unquote(query["uddg"][0])
    return url


def search_public_web(query: str, max_results: int = 5) -> list[SearchResult]:
    collected: list[SearchResult] = []
    for collector in (
        search_duckduckgo,
        search_google_news_rss,
        search_hacker_news,
        search_reddit,
        search_bing_rss,
        search_bing,
    ):
        try:
            collected.extend(collector(query, max_results=max_results))
        except (requests.RequestException, ValueError, ElementTree.ParseError):
            continue

    deduped = dedupe_results(collected)
    relevant = [result for result in deduped if relevance_score(query, result) > 0]
    ranked = sorted(relevant or deduped, key=lambda result: relevance_score(query, result), reverse=True)
    return ranked[:max_results]


def search_duckduckgo(query: str, max_results: int = 5) -> list[SearchResult]:
    response = requests.get(
        DUCKDUCKGO_HTML_URL,
        params={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []

    for result in soup.select(".result"):
        title_link = result.select_one(".result__a")
        if not title_link:
            continue

        title = title_link.get_text(" ", strip=True)
        url = normalize_ddg_url(title_link.get("href", ""))
        snippet_node = result.select_one(".result__snippet")
        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""

        if title and url.startswith(("http://", "https://")):
            results.append(SearchResult(title=title, url=url, snippet=snippet))

        if len(results) >= max_results:
            break

    return results


def search_bing_rss(query: str, max_results: int = 5) -> list[SearchResult]:
    response = requests.get(
        BING_SEARCH_URL,
        params={"q": query, "format": "rss"},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()

    root = ElementTree.fromstring(response.text)
    results: list[SearchResult] = []
    for item in root.findall("./channel/item"):
        title = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        snippet = " ".join((item.findtext("description") or "").split())
        if title and url.startswith(("http://", "https://")):
            results.append(SearchResult(title=title, url=url, snippet=snippet, source="Bing RSS"))
        if len(results) >= max_results:
            break
    return results


def search_google_news_rss(query: str, max_results: int = 5) -> list[SearchResult]:
    response = requests.get(
        GOOGLE_NEWS_RSS_URL,
        params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()

    root = ElementTree.fromstring(response.text)
    results: list[SearchResult] = []
    for item in root.findall("./channel/item"):
        title = clean_result_text(item.findtext("title") or "")
        url = (item.findtext("link") or "").strip()
        snippet = clean_result_text(item.findtext("description") or "")
        if title and url.startswith(("http://", "https://")):
            results.append(SearchResult(title=title, url=url, snippet=snippet, source="Google News RSS"))
        if len(results) >= max_results:
            break
    return results


def search_hacker_news(query: str, max_results: int = 5) -> list[SearchResult]:
    response = requests.get(
        HACKER_NEWS_SEARCH_URL,
        params={"query": query, "tags": "story", "hitsPerPage": max_results},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    results: list[SearchResult] = []
    for hit in payload.get("hits", []):
        title = clean_result_text(hit.get("title") or hit.get("story_title") or "")
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"
        points = hit.get("points")
        comments = hit.get("num_comments")
        snippet = f"Hacker News story. Points: {points or 0}. Comments: {comments or 0}."
        if title and url.startswith(("http://", "https://")):
            results.append(SearchResult(title=title, url=url, snippet=snippet, source="Hacker News"))
    return results[:max_results]


def search_reddit(query: str, max_results: int = 5) -> list[SearchResult]:
    response = requests.get(
        REDDIT_SEARCH_URL,
        params={"q": query, "sort": "relevance", "limit": max_results, "type": "link"},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()
    payload = response.json()

    results: list[SearchResult] = []
    for child in payload.get("data", {}).get("children", []):
        data = child.get("data", {})
        title = clean_result_text(data.get("title", ""))
        permalink = data.get("permalink", "")
        url = f"https://www.reddit.com{permalink}" if permalink.startswith("/") else data.get("url", "")
        snippet = clean_result_text(data.get("selftext", "")[:500] or data.get("subreddit_name_prefixed", "Reddit result"))
        if title and url.startswith(("http://", "https://")):
            results.append(SearchResult(title=title, url=url, snippet=snippet, source="Reddit"))
    return results[:max_results]


def search_bing(query: str, max_results: int = 5) -> list[SearchResult]:
    response = requests.get(
        BING_SEARCH_URL,
        params={"q": query},
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    results: list[SearchResult] = []

    for result in soup.select("li.b_algo"):
        title_link = result.select_one("h2 a")
        if not title_link:
            continue

        title = title_link.get_text(" ", strip=True)
        url = title_link.get("href", "")
        snippet_node = result.select_one(".b_caption p")
        snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""

        if title and url.startswith(("http://", "https://")):
            results.append(SearchResult(title=title, url=url, snippet=snippet, source="Bing"))

        if len(results) >= max_results:
            break

    return results


def domain_from_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed.netloc.lower().removeprefix("www.")


def dedupe_results(results: list[SearchResult]) -> list[SearchResult]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for result in results:
        key = result.url.rstrip("/")
        if not key or key in seen:
            continue
        seen.add(key)
        deduped.append(result)
    return deduped


def relevance_score(query: str, result: SearchResult) -> int:
    tokens = query_tokens(query)
    haystack = f"{result.title} {result.snippet} {domain_from_url(result.url)}".lower()
    return sum(1 for token in tokens if token in haystack)


def query_tokens(query: str) -> list[str]:
    cleaned = re.sub(r"\bsite:[^\s]+", " ", query.lower())
    cleaned = cleaned.replace(" or ", " ")
    return [
        token
        for token in re.findall(r"[a-z0-9][a-z0-9-]{2,}", cleaned)
        if token not in SEARCH_STOPWORDS
    ]


def clean_result_text(value: str) -> str:
    text = BeautifulSoup(unescape(value), "html.parser").get_text(" ", strip=True)
    return " ".join(text.split())
