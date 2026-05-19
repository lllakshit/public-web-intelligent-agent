from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

import requests

from public_web_agent.fetcher import extract_public_page
from public_web_agent.models import IntelligenceResult, WebItem
from public_web_agent.planner import build_search_plan
from public_web_agent.safety import assess_request
from public_web_agent.search import domain_from_url, search_public_web
from public_web_agent.storage import save_report
from public_web_agent.summarizer import summarize_text
from public_web_agent.writer import write_reports


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug[:72] or "report"


def run_intelligence(
    query: str,
    output_dir: Path,
    db_path: Path | None = None,
    max_results_per_query: int = 4,
    max_pages: int = 8,
    selected_domains: list[str] | None = None,
) -> IntelligenceResult:
    safety = assess_request(query)
    if not safety.allowed:
        raise ValueError(f"{safety.reason} {safety.suggestion}".strip())

    plan = build_search_plan(query, selected_domains=selected_domains)
    warnings: list[str] = []
    seen_urls: set[str] = set()
    items: list[WebItem] = []

    for search_query in plan.search_queries:
        try:
            results = search_public_web(search_query, max_results=max_results_per_query)
        except requests.RequestException as exc:
            warnings.append(f"Search failed for '{search_query}': {exc}")
            continue

        for result in results:
            normalized_url = result.url.rstrip("/")
            if normalized_url in seen_urls:
                continue
            seen_urls.add(normalized_url)
            items.append(
                WebItem(
                    title=result.title,
                    url=result.url,
                    snippet=result.snippet,
                    source=result.source,
                    domain=domain_from_url(result.url),
                )
            )

    fetched = 0
    for item in items:
        if fetched >= max_pages:
            item.fetch_status = "not fetched; page limit reached"
            item.summary = summarize_text(item.snippet, max_sentences=2)
            continue

        try:
            text, status = extract_public_page(item.url)
        except requests.RequestException as exc:
            text, status = "", f"fetch failed: {exc}"

        item.extracted_text = text
        item.fetch_status = status
        item.summary = summarize_text(text or item.snippet, max_sentences=3)
        if text:
            fetched += 1

    if not items:
        warnings.append("No public search results were collected. Try a narrower query or fewer domain restrictions.")

    report_id = f"{datetime.now().strftime('%Y%m%d-%H%M%S')}-{slugify(query)}"
    markdown_path, html_path, pdf_path, json_path = write_reports(report_id, query, plan, items, warnings, output_dir)
    result = IntelligenceResult(report_id, query, plan, items, warnings, markdown_path, html_path, pdf_path, json_path)

    json_path.write_text(json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    if db_path is not None:
        save_report(db_path, result)

    return result

