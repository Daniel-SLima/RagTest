from app.core.config import get_settings
from app.rag.docx_audit import audit_docx_directory


def main() -> None:
    settings = get_settings()
    stats = audit_docx_directory(settings.source_dir)

    print("RagTest DOCX structure audit")
    print(f"DOCX files: {len(stats)}")

    if not stats:
        print("No DOCX files found.")
        return

    affected = 0
    for item in stats:
        if item.has_structural_text_outside_body_paragraphs:
            affected += 1

        print()
        print(f"Source: {item.source}")
        print(
            "  body paragraphs        : "
            f"{item.nonempty_body_paragraphs}/{item.body_paragraphs} non-empty"
        )
        print(f"  body tables            : {item.body_tables}")
        print(f"  body table rows        : {item.body_table_rows}")
        print(f"  body table cells       : {item.body_table_cells}")
        print(f"  non-empty table cells  : {item.nonempty_body_table_cells}")
        print(f"  sections               : {item.sections}")
        print(
            "  header paragraphs      : "
            f"{item.nonempty_header_paragraphs}/{item.header_paragraphs} non-empty"
        )
        print(f"  header tables          : {item.header_tables}")
        print(
            "  footer paragraphs      : "
            f"{item.nonempty_footer_paragraphs}/{item.footer_paragraphs} non-empty"
        )
        print(f"  footer tables          : {item.footer_tables}")
        print(
            "  outside body paragraphs: "
            + (
                "yes"
                if item.has_structural_text_outside_body_paragraphs
                else "no"
            )
        )

    print()
    print(f"Files with structural content outside body paragraphs: {affected}")
    print("Audit is metadata-only: document text was not printed.")
