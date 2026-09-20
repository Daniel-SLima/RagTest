import re
from dataclasses import dataclass

from app.rag.citations import extract_citation_ids, validate_citations

_WORD_PATTERN = re.compile(r"[0-9A-Za-zÀ-ÿ]+", flags=re.UNICODE)
_LEADING_MARKUP_PATTERN = re.compile(
    r"^\s*(?:[-*+]\s+|\d+[.)]\s+|#{1,6}\s+)"
)


@dataclass(frozen=True, slots=True)
class CitationCoverage:
    valid: bool
    syntax_valid: bool
    total_claim_blocks: int
    cited_claim_blocks: int
    uncited_claim_blocks: int
    coverage: float
    reason: str | None = None


def _normalized_block(line: str) -> str:
    return _LEADING_MARKUP_PATTERN.sub("", line).strip()


def _is_claim_block(line: str) -> bool:
    normalized = _normalized_block(line)
    if not normalized:
        return False

    without_citations = re.sub(r"\[\d+\]", "", normalized).strip()
    words = _WORD_PATTERN.findall(without_citations)

    if len(words) < 3:
        return False

    if without_citations.endswith(":") and len(words) <= 10:
        return False

    return True


def validate_citation_coverage(
    answer: str,
    source_count: int,
) -> CitationCoverage:
    syntax = validate_citations(answer, source_count)

    claim_blocks = [
        line.strip()
        for line in answer.splitlines()
        if _is_claim_block(line)
    ]

    if not claim_blocks:
        return CitationCoverage(
            valid=False,
            syntax_valid=syntax.valid,
            total_claim_blocks=0,
            cited_claim_blocks=0,
            uncited_claim_blocks=0,
            coverage=0.0,
            reason="answer does not contain informative claim blocks",
        )

    cited = 0
    for block in claim_blocks:
        ids = extract_citation_ids(block)
        if ids and all(1 <= citation_id <= source_count for citation_id in ids):
            cited += 1

    total = len(claim_blocks)
    coverage = cited / total
    uncited = total - cited

    if not syntax.valid:
        reason = syntax.reason
    elif uncited:
        reason = "one or more informative answer blocks have no valid citation"
    else:
        reason = None

    return CitationCoverage(
        valid=syntax.valid and uncited == 0,
        syntax_valid=syntax.valid,
        total_claim_blocks=total,
        cited_claim_blocks=cited,
        uncited_claim_blocks=uncited,
        coverage=coverage,
        reason=reason,
    )
