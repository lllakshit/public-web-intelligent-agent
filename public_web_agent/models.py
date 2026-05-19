from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class SafetyDecision:
    allowed: bool
    reason: str = ""
    suggestion: str = ""


@dataclass(slots=True)
class SearchPlan:
    original_query: str
    intent: str
    search_queries: list[str]
    focus_domains: list[str]
    notes: list[str]


@dataclass(slots=True)
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str = "DuckDuckGo"


@dataclass(slots=True)
class WebItem:
    title: str
    url: str
    snippet: str
    source: str
    domain: str
    extracted_text: str = ""
    summary: str = ""
    fetch_status: str = "not_fetched"


@dataclass(slots=True)
class IntelligenceResult:
    report_id: str
    query: str
    plan: SearchPlan
    items: list[WebItem]
    warnings: list[str]
    markdown_path: Path
    html_path: Path
    pdf_path: Path
    json_path: Path

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "query": self.query,
            "plan": asdict(self.plan),
            "items": [asdict(item) for item in self.items],
            "warnings": self.warnings,
            "files": {
                "markdown": str(self.markdown_path),
                "html": str(self.html_path),
                "pdf": str(self.pdf_path),
                "json": str(self.json_path),
            },
        }


@dataclass(slots=True)
class StoredReport:
    report_id: str
    query: str
    intent: str
    created_at: str
    result_count: int
    warning_count: int
    markdown_content: str
    html_content: str
    pdf_bytes: bytes
    json_content: str

