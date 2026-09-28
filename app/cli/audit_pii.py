import argparse

from app.core.config import get_settings
from app.rag.pii_audit import audit_pii_directory


def main() -> None:
    parser = argparse.ArgumentParser(description="Auditoria local de dados pessoais em DOCX.")
    parser.add_argument("--subdir", default=None, help="Subpasta de SOURCE_DIR, ex.: chatscm")
    args = parser.parse_args()

    settings = get_settings()
    root = settings.source_dir / args.subdir if args.subdir else settings.source_dir
    reports = audit_pii_directory(root)

    print("RagTest PII audit (DOCX)")
    print(f"Arquivos: {len(reports)}")
    flagged = 0
    for report in reports:
        status = "ALERTA" if report.total else "limpo"
        flagged += 1 if report.total else 0
        print(f"- {report.source}: {status} | parágrafos={report.paragraphs} | {report.counts}")
        if report.total:
            print(f"  parágrafos para revisão manual: {list(report.paragraphs_with_matches)}")
    print(f"Arquivos com possíveis dados pessoais: {flagged}")
    print("A auditoria não imprime o texto dos documentos.")
