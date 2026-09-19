from collections import OrderedDict
import re
import unicodedata

from app.rag.vector_store import SearchHit

STOPWORDS = {
    "a", "ao", "aos", "as", "com", "como", "da", "das", "de", "do", "dos",
    "e", "em", "entre", "na", "nas", "no", "nos", "o", "os", "para", "por",
    "qual", "quais", "que", "sao", "se", "sem", "sobre", "uma", "um",
}


def _merge_overlapping_text(left: str, right: str, *, min_overlap: int = 40) -> str:
    if not left:
        return right
    if not right:
        return left
    if right in left:
        return left
    if left in right:
        return right

    max_overlap = min(len(left), len(right))
    for size in range(max_overlap, min_overlap - 1, -1):
        if left[-size:] == right[:size]:
            return left + right[size:]

    return left.rstrip() + "\n" + right.lstrip()


def _start_index(hit: SearchHit) -> int:
    value = hit.metadata.get("start_index")
    return value if isinstance(value, int) else 0


def _normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(
        character for character in value if not unicodedata.combining(character)
    )
    return value.lower()


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z0-9]+", _normalize(value))
        if len(token) >= 3 and token not in STOPWORDS
    }


def _related_token(left: str, right: str) -> bool:
    if left == right:
        return True
    return min(len(left), len(right)) >= 5 and left[:5] == right[:5]


def _coverage(query_tokens: set[str], target_tokens: set[str]) -> float:
    if not query_tokens or not target_tokens:
        return 0.0

    matched = sum(
        1
        for query_token in query_tokens
        if any(_related_token(query_token, target) for target in target_tokens)
    )
    return matched / len(query_tokens)


def group_hits_by_page(
    hits: list[SearchHit],
    *,
    max_group_chars: int = 5000,
) -> list[SearchHit]:
    groups: OrderedDict[tuple[str, str, int | str], list[SearchHit]] = OrderedDict()

    for hit in hits:
        key = (
            ("chunk", hit.source, hit.id)
            if hit.page is None
            else ("page", hit.source, hit.page)
        )
        groups.setdefault(key, []).append(hit)

    merged_hits: list[SearchHit] = []

    for members in groups.values():
        members.sort(key=_start_index)
        best = max(members, key=lambda item: item.score)

        merged_content = ""
        point_ids: list[str] = []
        for member in members:
            point_ids.append(member.id)
            merged_content = _merge_overlapping_text(merged_content, member.content)
            if len(merged_content) >= max_group_chars:
                merged_content = merged_content[:max_group_chars]
                break

        metadata = dict(best.metadata)
        metadata["grouped_point_ids"] = point_ids
        metadata["grouped_chunks"] = len(members)

        merged_hits.append(
            SearchHit(
                id=best.id,
                score=best.score,
                dense_score=max(
                    (item.dense_score for item in members if item.dense_score is not None),
                    default=None,
                ),
                sparse_score=max(
                    (item.sparse_score for item in members if item.sparse_score is not None),
                    default=None,
                ),
                content=merged_content,
                source=best.source,
                category=best.category,
                audience=best.audience,
                page=best.page,
                metadata=metadata,
                chunk_count=len(members),
            )
        )

    return sorted(merged_hits, key=lambda item: item.score, reverse=True)


def metadata_aware_rerank(
    query: str,
    hits: list[SearchHit],
    *,
    source_weight: float,
    content_weight: float,
) -> list[SearchHit]:
    query_tokens = _tokens(query)

    for hit in hits:
        source_text = " ".join(
            [
                hit.source,
                hit.category or "",
                hit.audience or "",
                str(hit.metadata.get("filename", "")),
            ]
        )
        source_coverage = _coverage(query_tokens, _tokens(source_text))
        content_coverage = _coverage(query_tokens, _tokens(hit.content))

        hit.rank_score = (
            hit.score
            + source_weight * source_coverage
            + content_weight * content_coverage
        )
        hit.metadata["source_lexical_coverage"] = round(source_coverage, 4)
        hit.metadata["content_lexical_coverage"] = round(content_coverage, 4)

    return sorted(
        hits,
        key=lambda item: item.rank_score if item.rank_score is not None else item.score,
        reverse=True,
    )


def _effective_score(hit: SearchHit) -> float:
    return hit.rank_score if hit.rank_score is not None else hit.score


def apply_relative_score_floor(
    hits: list[SearchHit],
    *,
    score_margin: float,
) -> list[SearchHit]:
    if not hits or score_margin <= 0:
        return hits

    floor = _effective_score(hits[0]) - score_margin
    return [hit for hit in hits if _effective_score(hit) >= floor]
