# Rastreamento (colo do útero e mama) — fontes a baixar

O ambiente automatizado não conseguiu baixar estes PDFs (bloqueio de rede para gov.br/cofen).
Baixe manualmente e salve nesta pasta com os nomes abaixo; depois rode o plano de sincronização.

| Salvar como | Documento | URL |
|---|---|---|
| `diretriz_rastreamento_colo_utero_2025.pdf` | Diretrizes Brasileiras para o Rastreamento do Câncer do Colo do Útero (MS, 2025 — DNA-HPV) | https://www.gov.br/saude/pt-br/assuntos/pcdt/r/rastreamento-cancer-do-colo-do-utero (espelho: https://www.cofen.gov.br/wp-content/uploads/2025/08/Rastreamento-Cancer-do-Colo-do-Utero.pdf) |
| `nota_tecnica_626_2025_mamografia.pdf` | Nota Técnica nº 626/2025-CGCAN/DECAN/SAES/MS — rastreamento do câncer de mama | https://www.gov.br/saude/pt-br/centrais-de-conteudo/publicacoes/notas-tecnicas/2025/nota-tecnica-no-626-2025-cgcan-decan-saes-ms.pdf |
| `inca_diretrizes_colo_utero_2016.pdf` | Diretrizes Brasileiras para o Rastreamento do Câncer do Colo do Útero, 2ª ed. (INCA, 2016) — Papanicolau | https://www.inca.gov.br (buscar pelo título) |

Depois de salvar:

    ragtest-plan-ingestion-sync
    ragtest-sync-ingestion

Não use `ragtest-ingest --recreate`.
