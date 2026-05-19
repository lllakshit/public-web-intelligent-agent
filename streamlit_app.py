from __future__ import annotations

from html import escape
from pathlib import Path

import streamlit as st

from public_web_agent.planner import INTENT_DOMAINS
from public_web_agent.pipeline import run_intelligence
from public_web_agent.storage import get_report, list_reports


ROOT_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT_DIR / "outputs"
DB_PATH = OUTPUT_DIR / "reports.sqlite3"

st.set_page_config(page_title="Public Web Intelligence Agent", page_icon=":mag:", layout="wide")


def inject_css() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #111827;
            --muted: #526077;
            --line: #d9e2f2;
            --panel: #ffffff;
            --bg: #f6f9ff;
            --blue: #2563eb;
            --blue-strong: #1d4ed8;
            --blue-soft: #eaf1ff;
            --green: #0f9f6e;
            --warn: #b45309;
        }

        html, body, [data-testid="stAppViewContainer"] {
            color-scheme: light;
            color: var(--ink);
            background: var(--bg);
        }

        [data-testid="stHeader"] {
            background: rgba(246, 249, 255, .92);
        }

        [data-testid="stSidebar"] {
            background: #fff;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"], [data-testid="stSidebar"] * {
            color: var(--ink) !important;
        }

        .block-container {
            max-width: 1240px;
            padding: 1.7rem 1.6rem 3rem;
        }

        .app-shell {
            display: grid;
            gap: 1.1rem;
        }

        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            border-bottom: 1px solid var(--line);
            padding-bottom: 1rem;
            margin-bottom: .3rem;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: .75rem;
        }

        .brand-mark {
            width: 38px;
            height: 38px;
            border-radius: 10px;
            background: #2563eb;
            position: relative;
            box-shadow: 0 10px 22px rgba(37, 99, 235, .18);
        }

        .brand-mark:after {
            content: "";
            position: absolute;
            inset: 9px;
            border: 4px solid #fff;
            border-radius: 999px;
        }

        .brand-title {
            font-size: 1.05rem;
            font-weight: 850;
            line-height: 1.1;
            color: var(--ink);
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: .45rem;
            border: 1px solid var(--line);
            border-radius: 999px;
            background: #fff;
            padding: .45rem .75rem;
            color: var(--muted);
            font-size: .88rem;
            font-weight: 700;
        }

        .dot {
            width: .55rem;
            height: .55rem;
            border-radius: 999px;
            background: var(--green);
        }

        .headline h1 {
            font-size: clamp(2rem, 4.4vw, 3.35rem);
            line-height: 1.05;
            letter-spacing: 0;
            margin: .6rem 0 .5rem;
            color: var(--ink);
        }

        .headline p {
            max-width: 780px;
            color: var(--muted);
            font-size: 1rem;
            line-height: 1.65;
            margin: 0;
        }

        .panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 1rem;
        }

        .mini-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: .75rem;
        }

        .mini-card {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: .9rem;
            min-height: 104px;
        }

        .mini-card strong {
            display: block;
            color: var(--ink);
            font-size: .95rem;
            margin-bottom: .4rem;
        }

        .mini-card span {
            color: var(--muted);
            font-size: .84rem;
            line-height: 1.45;
        }

        .report-card {
            border: 1px solid var(--line);
            border-radius: 8px;
            background: #fff;
            padding: .85rem;
            margin-bottom: .75rem;
        }

        .report-title {
            color: var(--ink);
            font-weight: 820;
            line-height: 1.3;
        }

        .report-meta {
            color: var(--muted);
            font-size: .82rem;
            margin-top: .25rem;
        }

        .small-note {
            color: var(--muted);
            font-size: .88rem;
            line-height: 1.5;
        }

        .query-list {
            margin: .35rem 0 0;
            padding-left: 1.1rem;
            color: var(--ink);
        }

        .query-list li {
            margin: .55rem 0;
            line-height: 1.5;
        }

        .blocked {
            border-left: 4px solid var(--warn);
            background: #fff8ed;
        }

        .stButton > button {
            min-height: 44px;
            border-radius: 8px !important;
            font-weight: 800 !important;
            background: var(--blue) !important;
            border: 1px solid var(--blue) !important;
            color: #fff !important;
            box-shadow: none !important;
        }

        .stButton > button p {
            white-space: nowrap;
        }

        .stButton > button:hover {
            background: var(--blue-strong) !important;
            border-color: var(--blue-strong) !important;
        }

        [data-testid="stDownloadButton"] button {
            min-height: 40px;
            border-radius: 8px !important;
            font-weight: 800 !important;
            background: #fff !important;
            border: 1px solid var(--line) !important;
            color: var(--ink) !important;
            box-shadow: none !important;
            padding: .45rem .55rem;
        }

        [data-testid="stDownloadButton"] button *,
        [data-testid="stDownloadButton"] button p {
            color: var(--ink) !important;
            white-space: nowrap;
            word-break: keep-all;
        }

        [data-testid="stTextArea"] textarea,
        [data-testid="stTextInput"] input,
        [data-testid="stNumberInput"] input {
            border-radius: 8px !important;
            border: 1px solid var(--line) !important;
            color: var(--ink) !important;
            background: #fff !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] {
            background: #fff !important;
            border: 1px solid var(--line) !important;
            border-radius: 8px !important;
            box-shadow: none !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] * {
            color: var(--ink) !important;
        }

        [data-baseweb="tag"] {
            background: #f3f7ff !important;
            color: var(--blue-strong) !important;
            border-radius: 999px !important;
            border: 1px solid #d7e3ff !important;
        }

        [data-baseweb="tag"] span,
        [data-baseweb="tag"] button {
            color: var(--blue-strong) !important;
        }

        @media (max-width: 900px) {
            .block-container {
                padding: 1rem .85rem 2.5rem;
            }

            .topbar {
                align-items: flex-start;
            }

            .mini-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }

        @media (max-width: 560px) {
            .topbar {
                flex-direction: column;
                align-items: flex-start;
                padding-top: 1.8rem;
                gap: .75rem;
            }

            .status-pill {
                align-self: flex-start;
            }

            .brand-title {
                font-size: .98rem;
            }

            .headline h1 {
                font-size: 2rem;
            }

            .mini-grid {
                grid-template-columns: 1fr;
            }

            [data-testid="stHorizontalBlock"] {
                gap: .5rem;
            }

            [data-testid="stDownloadButton"] button {
                font-size: .82rem;
                padding: .45rem .5rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def sidebar_controls() -> tuple[list[str], int, int]:
    st.sidebar.markdown(
        """
        <div class="brand">
            <div class="brand-mark"></div>
            <div class="brand-title">Public Web<br>Intelligence</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.sidebar.subheader("Search Controls")
    source_mode = st.sidebar.selectbox("Source preset", ["Auto by intent", "Career", "Funding", "Release", "People", "General"])
    max_results = st.sidebar.slider("Results per search", min_value=2, max_value=8, value=4)
    max_pages = st.sidebar.slider("Pages to extract", min_value=2, max_value=16, value=8)

    selected_domains: list[str] = []
    if source_mode != "Auto by intent":
        preset = source_mode.lower()
        selected_domains = st.sidebar.multiselect(
            "Focus domains",
            options=INTENT_DOMAINS[preset],
            default=INTENT_DOMAINS[preset],
        )

    st.sidebar.markdown(
        """
        <div class="panel small-note">
            <strong>No paid API keys.</strong><br>
            Uses public search pages and allowed public web extraction only.
        </div>
        """,
        unsafe_allow_html=True,
    )
    return selected_domains, max_results, max_pages


def render_recent_reports() -> None:
    reports = list_reports(DB_PATH, limit=6)
    if not reports:
        st.caption("No saved reports yet.")
        return

    for report in reports:
        st.markdown(
            f"""
            <div class="report-card">
                <div class="report-title">{escape(report.query)}</div>
                <div class="report-meta">{escape(report.intent)} - {report.result_count} results - {report.warning_count} warnings</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("View", key=f"view-{report.report_id}", use_container_width=True):
            st.session_state.active_report_id = report.report_id
            st.rerun()
        cols = st.columns(4)
        cols[0].download_button("MD", report.markdown_content, file_name=f"{report.report_id}.md", key=f"md-{report.report_id}", use_container_width=True)
        cols[1].download_button("HTML", report.html_content, file_name=f"{report.report_id}.html", key=f"html-{report.report_id}", use_container_width=True)
        cols[2].download_button("PDF", report.pdf_bytes, file_name=f"{report.report_id}.pdf", key=f"pdf-{report.report_id}", use_container_width=True)
        cols[3].download_button("JSON", report.json_content, file_name=f"{report.report_id}.json", key=f"json-{report.report_id}", use_container_width=True)


def render_active_report() -> None:
    active_id = st.session_state.get("active_report_id", "")
    report = get_report(DB_PATH, active_id) if active_id else None
    if report is None:
        st.caption("Open a saved report to view it here.")
        return
    st.markdown(f"### {report.query}")
    st.caption(f"{report.intent} - {report.result_count} results - {report.created_at}")
    st.markdown(report.markdown_content)


inject_css()
selected_domains, max_results, max_pages = sidebar_controls()

if "active_report_id" not in st.session_state:
    st.session_state.active_report_id = ""

st.markdown(
    """
    <div class="app-shell">
        <div class="topbar">
            <div class="brand">
                <div class="brand-mark"></div>
                <div class="brand-title">Public Web Intelligence Agent</div>
            </div>
            <div class="status-pill"><span class="dot"></span>Public web only</div>
        </div>
        <section class="headline">
            <h1>Search public sources, extract evidence, and produce a cited answer.</h1>
            <p>Use it for career opportunities, funding updates, public professional lookup, release monitoring, Reddit discussions, and general public web synthesis.</p>
        </section>
        <div class="mini-grid">
            <div class="mini-card"><strong>Plan</strong><span>Classifies intent and expands search terms.</span></div>
            <div class="mini-card"><strong>Collect</strong><span>Uses public search and source pages.</span></div>
            <div class="mini-card"><strong>Extract</strong><span>Reads allowed pages and records limits.</span></div>
            <div class="mini-card"><strong>Report</strong><span>Saves cited Markdown, HTML, PDF, and JSON.</span></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

main_col, side_col = st.columns([1.55, 1], gap="large")

with main_col:
    with st.container(border=True):
        st.subheader("Ask the agent")
        query = st.text_area(
            "Public web request",
            placeholder="Example: find remote AI product manager roles in India from YC companies",
            height=135,
        )
        run_clicked = st.button("Run Public Search", type="primary", use_container_width=True, disabled=not query.strip())
        st.markdown(
            '<p class="small-note">The agent blocks piracy, cracking, credential misuse, private personal tracing, and login-gated scraping requests.</p>',
            unsafe_allow_html=True,
        )

    if run_clicked:
        with st.status("Running public web intelligence...", expanded=True) as status:
            try:
                status.write("Planning intent and search queries.")
                status.write("Searching public web results.")
                status.write("Extracting readable public pages.")
                result = run_intelligence(
                    query,
                    output_dir=OUTPUT_DIR,
                    db_path=DB_PATH,
                    max_results_per_query=max_results,
                    max_pages=max_pages,
                    selected_domains=selected_domains or None,
                )
            except ValueError as exc:
                status.update(label="Request blocked", state="error")
                st.markdown(f'<div class="panel blocked">{escape(str(exc))}</div>', unsafe_allow_html=True)
                st.stop()
            except Exception as exc:
                status.update(label="Run failed", state="error")
                st.error(str(exc))
                st.stop()
            status.update(label="Report created", state="complete")

        st.session_state.active_report_id = result.report_id
        st.success(f"Created report with {len(result.items)} result(s).")
        if result.warnings:
            with st.expander("Warnings", expanded=True):
                for warning in result.warnings:
                    st.warning(warning)

        st.subheader("Downloads")
        cols = st.columns(4)
        cols[0].download_button("Markdown", result.markdown_path.read_bytes(), file_name=result.markdown_path.name, use_container_width=True)
        cols[1].download_button("HTML", result.html_path.read_bytes(), file_name=result.html_path.name, use_container_width=True)
        cols[2].download_button("PDF", result.pdf_path.read_bytes(), file_name=result.pdf_path.name, use_container_width=True)
        cols[3].download_button("JSON", result.json_path.read_bytes(), file_name=result.json_path.name, use_container_width=True)

with side_col:
    with st.container(border=True):
        st.subheader("Good test queries")
        st.markdown(
            """
            <ul class="query-list">
                <li>find remote AI product manager roles in India from YC companies</li>
                <li>latest Y Combinator healthcare startup funding updates</li>
                <li>public discussion of Cursor AI pricing changes reddit</li>
                <li>GitHub Actions release updates breaking changes</li>
                <li>who is Andrej Karpathy public profile talks projects</li>
            </ul>
            """
            ,
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.subheader("Recent reports")
        render_recent_reports()

st.subheader("Report viewer")
render_active_report()
