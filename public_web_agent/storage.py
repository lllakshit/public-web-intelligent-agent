from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from public_web_agent.models import IntelligenceResult, StoredReport


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY,
            query TEXT NOT NULL,
            intent TEXT NOT NULL,
            created_at TEXT NOT NULL,
            result_count INTEGER NOT NULL,
            warning_count INTEGER NOT NULL,
            markdown_content TEXT NOT NULL,
            html_content TEXT NOT NULL,
            pdf_bytes BLOB NOT NULL,
            json_content TEXT NOT NULL
        )
        """
    )
    return connection


def save_report(db_path: Path, result: IntelligenceResult) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO reports (
                report_id, query, intent, created_at, result_count, warning_count,
                markdown_content, html_content, pdf_bytes, json_content
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.report_id,
                result.query,
                result.plan.intent,
                datetime.now(UTC).isoformat(),
                len(result.items),
                len(result.warnings),
                result.markdown_path.read_text(encoding="utf-8"),
                result.html_path.read_text(encoding="utf-8"),
                result.pdf_path.read_bytes(),
                result.json_path.read_text(encoding="utf-8"),
            ),
        )


def list_reports(db_path: Path, limit: int = 8) -> list[StoredReport]:
    with connect(db_path) as connection:
        rows = connection.execute(
            """
            SELECT report_id, query, intent, created_at, result_count, warning_count,
                   markdown_content, html_content, pdf_bytes, json_content
            FROM reports
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [StoredReport(*row) for row in rows]


def get_report(db_path: Path, report_id: str) -> StoredReport | None:
    with connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT report_id, query, intent, created_at, result_count, warning_count,
                   markdown_content, html_content, pdf_bytes, json_content
            FROM reports
            WHERE report_id = ?
            """,
            (report_id,),
        ).fetchone()
    return StoredReport(*row) if row else None

