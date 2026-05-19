from __future__ import annotations

import re
from collections import Counter


STOPWORDS = {
    "about", "after", "also", "from", "have", "into", "more", "over", "than", "that", "their",
    "there", "these", "this", "with", "were", "will", "would", "your", "they", "them", "been",
    "being", "because", "which", "while", "where", "what", "when", "each", "such", "using",
}


def split_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]


def summarize_text(text: str, max_sentences: int = 3) -> str:
    text = " ".join((text or "").split())
    if not text:
        return "No readable text was available; use the linked source for verification."

    sentences = split_sentences(text)
    if len(sentences) <= max_sentences:
        return " ".join(sentences)

    words = [word for word in re.findall(r"[a-zA-Z][a-zA-Z-]{3,}", text.lower()) if word not in STOPWORDS]
    scores = Counter(words)

    ranked = sorted(
        sentences,
        key=lambda sentence: sum(scores[word] for word in re.findall(r"[a-zA-Z][a-zA-Z-]{3,}", sentence.lower())),
        reverse=True,
    )
    selected = ranked[:max_sentences]
    return " ".join(sentence for sentence in sentences if sentence in selected)


def build_answer(query: str, summaries: list[str]) -> str:
    useful = [summary for summary in summaries if summary and not summary.startswith("No readable")]
    if not useful:
        return f"I found public web references for '{query}', but the pages did not expose enough readable text for a strong synthesis."
    combined = " ".join(useful[:6])
    return summarize_text(combined, max_sentences=4)

