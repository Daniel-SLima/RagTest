from collections import OrderedDict

from app.rag.vector_store import SearchHit


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


def group_hits_by_page(
    hits: list[SearchHit],
    *,
    max_group_chars: int = 5000,
) -> list[SearchHit]:
    """Merge chunks from the same PDF page while preserving their text order.

    Chunks without page metadata are kept independent because grouping an entire
    DOCX by source could create an oversized context block.
    """

    groups: OrderedDict[tuple[str, str, int | str], list[SearchHit]] = OrderedDict()

    for hit in hits:
        if hit.page is None:
            key = ("chunk", hit.source, hit.id)
        else:
            key = ("page", hit.source, hit.page)
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


def apply_relative_score_floor(
    hits: list[SearchHit],
    *,
    score_margin: float,
) -> list[SearchHit]:
    """Drop candidates that are far below the best semantic match.

    This is relative instead of using one global score threshold because dense
    similarity scales vary by query and embedding model.
    """

    if not hits or score_margin <= 0:
        return hits

    floor = hits[0].score - score_margin
    return [hit for hit in hits if hit.score >= floor]
