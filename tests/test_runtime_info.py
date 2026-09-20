from types import SimpleNamespace

from app.cli.runtime_info import _collection_lines, _enum_value


def test_enum_value_prefers_enum_value_attribute() -> None:
    assert _enum_value(SimpleNamespace(value="Cosine")) == "Cosine"


def test_collection_lines_include_dense_sparse_metadata_and_counts() -> None:
    info = SimpleNamespace(
        config=SimpleNamespace(
            params=SimpleNamespace(
                vectors={
                    "dense": SimpleNamespace(
                        size=384,
                        distance=SimpleNamespace(value="Cosine"),
                    )
                },
                sparse_vectors={
                    "sparse": SimpleNamespace(
                        modifier=SimpleNamespace(value="Idf"),
                    )
                },
            ),
            metadata={"embedding_model": "example-model"},
        ),
        points_count=767,
        indexed_vectors_count=767,
    )

    lines = _collection_lines(info)

    assert "  dense dense: size=384 distance=Cosine" in lines
    assert "  sparse sparse: modifier=Idf" in lines
    assert "  metadata: {'embedding_model': 'example-model'}" in lines
    assert "  points_count: 767" in lines
    assert "  indexed_vectors_count: 767" in lines
