"""The Law — deterministic content gate for The Image That Speaks demo.

Checks beast_output against forbidden_claims rules. Does not hallucinate.
Does not worship. Is incorruptible.
"""

from __future__ import annotations

import re


def check_forbidden_claims(state: dict) -> str:
    """Check content against deterministic rules.

    Args:
        state: Graph state with beast_output and forbidden_claims keys.

    Returns:
        Structured findings as text.
    """
    beast_output = state.get("beast_output", "")
    forbidden_claims = state.get("forbidden_claims")
    if not forbidden_claims:
        return "No rules loaded — the Law is silent."

    findings: list[str] = []
    text_lower = beast_output.lower()

    # Check certainty markers
    for marker in forbidden_claims.get("certainty_markers", []):
        if marker.lower() in text_lower:
            findings.append(f"CERTAINTY_VIOLATION: '{marker}' found in text")

    # Check forbidden phrases
    for phrase in forbidden_claims.get("forbidden_phrases", []):
        if phrase.lower() in text_lower:
            findings.append(f"FORBIDDEN_CLAIM: '{phrase}' found in text")

    # Check unsourced statistics
    pattern = forbidden_claims.get("unsourced_stat_pattern", "")
    if pattern:
        stats = re.findall(pattern, beast_output)
        if stats:
            findings.append(
                f"UNSOURCED_STATISTICS: {len(stats)} percentage claims "
                f"found without attribution: {', '.join(stats)}"
            )

    # Check for missing citations
    if forbidden_claims.get("require_citations", False):
        citation_patterns = [r"\[\d+\]", r"\(\w+ et al", r"doi:", r"http"]
        has_citation = any(
            re.search(p, beast_output, re.IGNORECASE) for p in citation_patterns
        )
        if not has_citation:
            findings.append("MISSING_CITATIONS: No references or citations found")

    if not findings:
        return "The Law found no violations. The content passes."

    header = f"The Law found {len(findings)} violation(s):"
    return header + "\n" + "\n".join(f"  - {f}" for f in findings)
