# Public Web Intelligence Agent

A no-paid-API Streamlit agent for public web research. It plans search queries, searches public web results, extracts allowed page text, creates local summaries, and saves cited reports as Markdown, HTML, PDF, and JSON.

## What It Does

- Searches public web sources without paid API keys.
- Routes requests by intent: general research, career opportunities, funding/startups, release updates, and public professional lookup.
- Extracts text from allowed public pages with `trafilatura` and `beautifulsoup4`.
- Summarizes locally with extractive Python logic.
- Saves report history in SQLite.
- Exports Markdown, HTML, PDF, and raw JSON.

## Safety Boundary

The agent blocks requests for pirated/cracked software, license keys, credential theft, private personal tracing, and login-gated scraping. It can still suggest legal alternatives or public information sources.

## Local Setup

```powershell
cd F:\automations\public-web-intelligent-agent
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## CLI

```powershell
python cli.py "find remote AI product manager roles in India" --max-results 5
```

## Deployment Notes

- Entry point: `streamlit_app.py`
- No secrets are required.
- SQLite history is local to the deployment environment and may reset on free hosting restarts.
- Keep search volume modest to avoid rate limits or blocks from public sources.

