# Avaliação do Retrieval

## 0.5.1 — baseline dense

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.714

## 0.5.2 — reranking lexical

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.786

Melhor resultado medido antes da correção de ingestão.

## 0.5.3 — dense + BM25 + RRF

- HitRate@5: 0.714 (5/7)
- MRR@5: 0.607

## 0.5.4 — BM25 enriquecido com metadados

- HitRate@5: 0.857 (6/7)
- MRR@5: 0.690

## Diagnóstico 0.5.5 — cobertura do corpus

A auditoria comprovou que:

- direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf:
  28 páginas, 0 páginas com texto, 0 caracteres e 0 chunks.
- caderneta_gestante_8ed_rev.pdf:
  50 páginas, 47 com texto.
- caderneta_saude_pessoa_idosa_5ed_1re.pdf:
  64 páginas, 63 com texto.

A consulta 7 não era um teste válido de qualidade do retrieval porque a fonte esperada não fazia parte do índice.

## 0.5.6 — OCR seletivo local

A versão 0.5.6 adiciona OCR somente nas páginas em que o extrator normal não encontrou texto.

Tecnologia:

- Tesseract OCR;
- idioma por;
- PyMuPDF para renderizar a página;
- OCR executado localmente no container;
- metadata extraction_method identifica text, ocr, empty ou docx.

Após atualizar, executar primeiro:

    docker compose run --rm api ragtest-inspect --source direitos_saude

Se o PDF passar a gerar texto, recriar a collection:

    docker compose run --rm api ragtest-ingest --recreate

Depois repetir a avaliação. Como o corpus terá mudado, os resultados posteriores não devem ser comparados como se fossem exatamente a mesma condição experimental das versões anteriores; deve-se registrar que houve correção da cobertura do corpus.
