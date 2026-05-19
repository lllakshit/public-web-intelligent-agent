from __future__ import annotations

import argparse
from pathlib import Path

from public_web_agent.pipeline import run_intelligence


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a public web intelligence report.")
    parser.add_argument("query", help="Research request to investigate.")
    parser.add_argument("--max-results", type=int, default=5, help="Results per planned search query.")
    parser.add_argument("--max-pages", type=int, default=8, help="Maximum pages to extract.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for generated reports.")
    args = parser.parse_args()

    result = run_intelligence(
        args.query,
        output_dir=Path(args.output_dir),
        max_results_per_query=args.max_results,
        max_pages=args.max_pages,
    )

    print(f"Report ID: {result.report_id}")
    print(f"Intent: {result.plan.intent}")
    print(f"Results: {len(result.items)}")
    print(f"Markdown: {result.markdown_path}")
    print(f"HTML: {result.html_path}")
    print(f"PDF: {result.pdf_path}")
    print(f"JSON: {result.json_path}")
    if result.warnings:
        print("Warnings:")
        for warning in result.warnings:
            print(f"- {warning}")


if __name__ == "__main__":
    main()

