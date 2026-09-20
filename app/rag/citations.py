import re
from dataclasses import dataclass


_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


@dataclass(frozen=True, slots=True)
class CitationValidation:
    valid: bool
    citation_ids: tuple[int, ...]
    invalid_ids: tuple[int, ...]
    reason: str | None = None


def extract_citation_ids(answer: str) -> tuple[int, ...]:
    ids = {int(match) for match in _CITATION_PATTERN.findall(answer)}
    return tuple(sorted(ids))


def validate_citations(
    answer: str,
    source_count: int,
    *,
    require_at_least_one: bool = True,
) -> CitationValidation:
    citation_ids = extract_citation_ids(answer)
    invalid_ids = tuple(
        citation_id
        for citation_id in citation_ids
        if citation_id < 1 or citation_id > source_count
    )

    if invalid_ids:
        return CitationValidation(
            valid=False,
            citation_ids=citation_ids,
            invalid_ids=invalid_ids,
            reason="answer contains citation ids outside the available source range",
        )

    if require_at_least_one and source_count > 0 and not citation_ids:
        return CitationValidation(
            valid=False,
            citation_ids=citation_ids,
            invalid_ids=(),
            reason="answer does not contain a verifiable source citation",
        )

    return CitationValidation(
        valid=True,
        citation_ids=citation_ids,
        invalid_ids=(),
    )
