from __future__ import annotations

from urllib.parse import quote_plus

from public_web_agent.models import SearchPlan


INTENT_DOMAINS = {
    "career": ["ycombinator.com/jobs", "wellfound.com", "remoteok.com", "greenhouse.io", "lever.co"],
    "funding": ["ycombinator.com", "techcrunch.com", "crunchbase.com", "grantwatch.com", "grants.gov"],
    "release": ["github.com", "docs.github.com", "changelog.com", "developers.googleblog.com", "openai.com"],
    "people": ["linkedin.com", "github.com", "x.com", "medium.com", "reddit.com"],
    "general": ["reddit.com", "wikipedia.org", "github.com", "medium.com", "news.ycombinator.com"],
}


def detect_intent(query: str) -> str:
    q = query.lower()
    if any(term in q for term in ["job", "career", "hiring", "internship", "role", "opportunity", "opening"]):
        return "career"
    if any(term in q for term in ["funding", "fundraise", "fundraising", "grant", "accelerator", "y combinator", "yc"]):
        return "funding"
    if any(term in q for term in ["release", "changelog", "update", "breaking change", "api change"]):
        return "release"
    if any(term in q for term in ["find person", "profile", "linkedin", "who is", "people"]):
        return "people"
    return "general"


def build_search_plan(query: str, selected_domains: list[str] | None = None) -> SearchPlan:
    intent = detect_intent(query)
    domains = selected_domains or INTENT_DOMAINS[intent]
    cleaned_query = " ".join(query.split())
    search_queries = [cleaned_query]

    if intent == "career":
        search_queries.extend([
            f"{cleaned_query} jobs OR hiring",
            f"{cleaned_query} site:ycombinator.com/jobs",
            f"{cleaned_query} site:lever.co OR site:greenhouse.io",
        ])
    elif intent == "funding":
        search_queries.extend([
            f"{cleaned_query} funding announcement",
            f"{cleaned_query} accelerator grant application",
            f"{cleaned_query} site:ycombinator.com",
        ])
    elif intent == "release":
        search_queries.extend([
            f"{cleaned_query} changelog",
            f"{cleaned_query} release notes",
            f"{cleaned_query} migration guide",
        ])
    elif intent == "people":
        search_queries.extend([
            f"{cleaned_query} public profile",
            f"{cleaned_query} site:linkedin.com/in OR site:github.com",
            f"{cleaned_query} interviews OR talks OR publications",
        ])
    else:
        search_queries.extend([
            f"{cleaned_query} reddit discussion",
            f"{cleaned_query} official documentation",
            f"{cleaned_query} latest update",
        ])

    for domain in domains[:4]:
        search_queries.append(f"{cleaned_query} site:{domain}")

    unique_queries = []
    for item in search_queries:
        if item not in unique_queries:
            unique_queries.append(item)

    return SearchPlan(
        original_query=query,
        intent=intent,
        search_queries=unique_queries[:8],
        focus_domains=domains,
        notes=[f"Search URL preview: https://duckduckgo.com/?q={quote_plus(cleaned_query)}"],
    )

