# RagTest

Módulo RAG reutilizável via API.

## Fase 0.5.6 — OCR seletivo

A auditoria do corpus encontrou a causa da consulta de direitos/deveres:

    direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf
    28 páginas
    0 páginas com texto
    0 caracteres
    0 chunks

A versão 0.5.6 adiciona fallback de OCR local somente para páginas onde a extração normal retorna vazio.

Stack de OCR:

- Tesseract OCR;
- language pack português;
- PyMuPDF para renderização;
- pytesseract;
- metadata extraction_method para auditoria.

## Atualizar

No .env adicione:

    PDF_OCR_ENABLED=true
    PDF_OCR_LANGUAGE=por
    PDF_OCR_DPI=200
    PDF_OCR_TIMEOUT_SECONDS=60

Depois:

    git pull origin main
    docker compose down
    docker compose up --build -d

Primeiro audite sem reindexar:

    docker compose run --rm api ragtest-inspect --source direitos_saude

A coluna OCR deve mostrar quantas páginas precisaram de reconhecimento.

Se houver texto/chunks:

    docker compose run --rm api ragtest-ingest --recreate

Depois:

    docker compose run --rm api ragtest-search "Quais são os direitos e deveres da pessoa usuária da saúde?" --limit 5
    docker compose run --rm api ragtest-evaluate-retrieval

O OCR é executado localmente no container. Nenhuma página é enviada ao Gemini durante a extração.

## Histórico experimental

    0.5.1  HitRate@5=0.857  MRR@5=0.714
    0.5.2  HitRate@5=0.857  MRR@5=0.786
    0.5.3  HitRate@5=0.714  MRR@5=0.607
    0.5.4  HitRate@5=0.857  MRR@5=0.690

Os resultados anteriores foram obtidos com a carta de direitos fora do índice; isso deve ser explicitado na análise do TCC.
