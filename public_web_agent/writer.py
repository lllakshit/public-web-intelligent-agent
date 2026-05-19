from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from textwrap import wrap

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from public_web_agent.models import IntelligenceResult, SearchPlan, WebItem
from public_web_agent.summarizer import build_answer


def write_reports(
    report_id: str,
    query: str,
    plan: SearchPlan,
    items: list[WebItem],
    warnings: list[str],
    output_dir: Path,
) -> tuple[Path, Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    base = output_dir / report_id
    answer = build_answer(query, [item.summary for item in items])

    markdown = render_markdown(query, plan, items, warnings, answer)
    html = render_html(query, plan, items, warnings, answer)
    raw_json = {
        "report_id": report_id,
        "created_at": datetime.now(UTC).isoformat(),
        "query": query,
        "plan": {
            "intent": plan.intent,
            "search_queries": plan.search_queries,
            "focus_domains": plan.focus_domains,
            "notes": plan.notes,
        },
        "answer": answer,
        "warnings": warnings,
        "items": [asdict(item) for item in items],
    }

    markdown_path = base.with_suffix(".md")
    html_path = base.with_suffix(".html")
    pdf_path = base.with_suffix(".pdf")
    json_path = base.with_suffix(".json")

    markdown_path.write_text(markdown, encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    json_path.write_text(json.dumps(raw_json, ensure_ascii=False, indent=2), encoding="utf-8")
    write_pdf(pdf_path, query, plan, items, warnings, answer)
    return markdown_path, html_path, pdf_path, json_path


def render_markdown(query: str, plan: SearchPlan, items: list[WebItem], warnings: list[str], answer: str) -> str:
    lines = [
        f"# Public Web Intelligence Report: {query}",
        "",
        f"- Intent: {plan.intent}",
        f"- Sources reviewed: {len(items)}",
        "",
        "## Synthesis",
        "",
        answer,
        "",
        "## Evidence",
        "",
    ]

    for index, item in enumerate(items, start=1):
        lines.extend([
            f"### {index}. {item.title}",
            "",
            f"- Domain: {item.domain}",
            f"- URL: {item.url}",
            f"- Status: {item.fetch_status}",
            "",
            item.summary,
            "",
        ])

    if warnings:
        lines.extend(["## Warnings", ""])
        lines.extend(f"- {warning}" for warning in warnings)
        lines.append("")

    lines.extend([
        "## Search Queries",
        "",
        *[f"- {query_item}" for query_item in plan.search_queries],
    ])
    return "\n".join(lines)


def render_html(query: str, plan: SearchPlan, items: list[WebItem], warnings: list[str], answer: str) -> str:
    evidence = "\n".join(
        f"""
        <article class="item">
            <div class="meta">{escape(item.domain)} · {escape(item.fetch_status)}</div>
            <h2>{escape(item.title)}</h2>
            <p>{escape(item.summary)}</p>
            <a href="{escape(item.url)}">{escape(item.url)}</a>
        </article>
        """
        for item in items
    )
    warnings_html = "".join(f"<li>{escape(warning)}</li>" for warning in warnings) or "<li>No warnings.</li>"
    queries_html = "".join(f"<li>{escape(search_query)}</li>" for search_query in plan.search_queries)
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(query)}</title>
<style>
html {{ color-scheme: light; }}
body {{ margin: 0; background: #f5f8ff; color: #10182f; font-family: Arial, sans-serif; line-height: 1.62; }}
main {{ max-width: 920px; margin: 0 auto; padding: 32px 18px 48px; }}
h1 {{ font-size: clamp(28px, 5vw, 46px); line-height: 1.08; margin: 0 0 12px; }}
h2 {{ font-size: 20px; margin: 8px 0; }}
.panel, .item {{ background: #fff; border: 1px solid #d8e0ef; border-radius: 8px; padding: 18px; margin: 16px 0; }}
.meta {{ color: #53627e; font-size: 14px; font-weight: 700; }}
a {{ color: #1f5fbf; word-break: break-word; }}
ul {{ padding-left: 20px; }}
@media (max-width: 560px) {{ main {{ padding: 22px 12px 36px; }} .panel, .item {{ padding: 14px; }} }}
</style>
</head>
<body>
<main>
<h1>{escape(query)}</h1>
<div class="meta">Intent: {escape(plan.intent)} · Sources reviewed: {len(items)}</div>
<section class="panel"><h2>Synthesis</h2><p>{escape(answer)}</p></section>
<section>{evidence}</section>
<section class="panel"><h2>Warnings</h2><ul>{warnings_html}</ul></section>
<section class="panel"><h2>Search Queries</h2><ul>{queries_html}</ul></section>
</main>
</body>
</html>"""


def write_pdf(path: Path, query: str, plan: SearchPlan, items: list[WebItem], warnings: list[str], answer: str) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=.65 * inch, leftMargin=.65 * inch, topMargin=.65 * inch, bottomMargin=.65 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleZero", parent=styles["Title"], textColor=colors.HexColor("#10182f"), fontSize=20, leading=24)
    heading_style = ParagraphStyle("HeadingZero", parent=styles["Heading2"], textColor=colors.HexColor("#10182f"), fontSize=13, leading=16)
    body_style = ParagraphStyle("BodyZero", parent=styles["BodyText"], textColor=colors.HexColor("#1f2a44"), fontSize=9.5, leading=13)
    meta_style = ParagraphStyle("MetaZero", parent=styles["BodyText"], textColor=colors.HexColor("#53627e"), fontSize=8.5, leading=12)

    story = [
        Paragraph(pdf_safe(query), title_style),
        Paragraph(pdf_safe(f"Intent: {plan.intent} | Sources reviewed: {len(items)}"), meta_style),
        Spacer(1, 12),
        Paragraph("Synthesis", heading_style),
        Paragraph(pdf_safe(answer), body_style),
        Spacer(1, 10),
        Paragraph("Evidence", heading_style),
    ]

    for index, item in enumerate(items, start=1):
        story.extend([
            Paragraph(pdf_safe(f"{index}. {item.title}"), heading_style),
            Paragraph(pdf_safe(f"{item.domain} | {item.fetch_status} | {item.url}"), meta_style),
            Paragraph(pdf_safe(item.summary), body_style),
            Spacer(1, 8),
        ])

    if warnings:
        story.append(Paragraph("Warnings", heading_style))
        for warning in warnings:
            story.append(Paragraph(pdf_safe(f"- {warning}"), body_style))

    doc.build(story)


def pdf_safe(text: str) -> str:
    wrapped = "\n".join(wrap(" ".join((text or "").split()), width=110))
    return escape(wrapped.encode("latin-1", "replace").decode("latin-1"))
