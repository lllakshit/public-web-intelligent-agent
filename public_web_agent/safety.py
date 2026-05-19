from __future__ import annotations

import re

from public_web_agent.models import SafetyDecision


BLOCKED_PATTERNS = [
    r"\bcrack(?:ed)?\b",
    r"\bkeygen\b",
    r"\bserial\s*key\b",
    r"\blicen[cs]e\s*key\b",
    r"\bpirat(?:e|ed|ing)\b",
    r"\btorrent\b",
    r"\bwarez\b",
    r"\bpassword\s*(dump|list|leak)\b",
    r"\bcredential\s*(dump|leak|list)\b",
    r"\bbypass\s+(paywall|login|activation|license)\b",
]

PRIVATE_TRACING_PATTERNS = [
    r"\bhome\s+address\b",
    r"\bphone\s+number\b",
    r"\bprivate\s+email\b",
    r"\btrack\s+(this|a)\s+person\b",
    r"\bstalk\b",
]


def assess_request(query: str) -> SafetyDecision:
    normalized = query.strip().lower()
    if not normalized:
        return SafetyDecision(False, "Enter a public web research request.", "Try a topic, company, role, or public domain search.")

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, normalized):
            return SafetyDecision(
                False,
                "This request asks for piracy, cracking, credential misuse, or access bypass help.",
                "Ask for legal alternatives, official trials, open-source replacements, or pricing comparisons.",
            )

    for pattern in PRIVATE_TRACING_PATTERNS:
        if re.search(pattern, normalized):
            return SafetyDecision(
                False,
                "This request targets private personal information.",
                "Ask for public professional profiles, official biographies, or public work history instead.",
            )

    return SafetyDecision(True)

