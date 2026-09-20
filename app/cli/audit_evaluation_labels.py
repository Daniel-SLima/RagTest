from app.evaluation import EVALUATION_DATASET_VERSION, select_retrieval_cases
from app.evaluation.labels import source_label_summary


def main() -> None:
    cases = select_retrieval_cases("all")
    summary = source_label_summary(cases)

    print("RagTest evaluation label audit")
    print(f"Dataset                 : {EVALUATION_DATASET_VERSION}")
    print(f"Total cases             : {summary['total_cases']}")
    print(f"Legacy expected_sources : {summary['legacy_cases']}")
    print(f"Legacy multi-source     : {summary['legacy_multi_source_cases']}")
    print(f"Explicit semantic cases : {summary['explicit_cases']}")
    print(
        "Explicit acceptable    : "
        f"{summary['explicit_with_acceptable']}"
    )
    print(f"Explicit required       : {summary['explicit_with_required']}")
    print()
    print(
        "Interpretation: expected_sources in the frozen v1 dataset is a "
        "legacy ambiguous label."
    )
    print(
        "Historical HitRate/MRR/SourceRecall/SourceNDCG remain preserved, "
        "but multi-source expected_sources must not be described as a "
        "manually verified complete relevance set."
    )
    print(
        "Future datasets should use acceptable_sources for OR alternatives "
        "and required_sources only when all listed sources are intentionally "
        "required for coverage."
    )
