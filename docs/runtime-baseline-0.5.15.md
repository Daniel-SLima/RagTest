# Runtime baseline — RagTest 0.5.15

Baseline capturada em 2026-09-20 antes do pinning adicional.

## Aplicação e bibliotecas principais

- RagTest: `0.5.15`
- FastEmbed: `0.8.0`
- qdrant-client: `1.19.1`
- google-genai: `1.75.0`
- FastAPI: `0.141.1`
- PyMuPDF: `1.28.2`
- PyPDF: `6.19.0`

## Retrieval e embeddings

- dense model: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
- sparse model: `Qdrant/bm25`
- sparse language: `portuguese`
- retrieval mode: `dense-rerank`
- chunk size: `1000`
- chunk overlap: `200`

## Qdrant

- servidor: `1.19.1`
- commit reportado: `6ab21cac18ebb6f4ae29102c7f8f5cc11affd5de`
- collection: `ragtest_documents`
- dense vector: nome `dense`, dimensão `384`, distância `Cosine`
- sparse vector: nome `sparse`, modifier `idf`
- points count: `767`
- indexed vectors count: `767`
- metadata da collection: ausente

## Decisão de pinning

A partir desta baseline:

- `fastembed` é fixado em `0.8.0`;
- `qdrant-client` é fixado em `1.19.1`;
- a imagem Qdrant padrão é fixada em `qdrant/qdrant:v1.19.1`.

Esses pins reproduzem as versões efetivamente observadas no runtime que já opera sobre os 767 pontos atuais. Não é necessário reindexar a collection apenas por aplicar estes pins.

A ausência de metadata de compatibilidade na collection continua sendo uma pendência separada; não será preenchida retroativamente sem uma regra explícita de versionamento/migração.


## Validação pós-pinning

Após trocar o runtime para versões exatas e reconstruir a imagem, o fingerprint permaneceu idêntico:

- FastEmbed: `0.8.0`
- qdrant-client: `1.19.1`
- Qdrant Server: `1.19.1`
- commit Qdrant: `6ab21cac18ebb6f4ae29102c7f8f5cc11affd5de`
- dense: dimensão `384`, distância `Cosine`
- sparse: modifier `idf`
- points count: `767`
- indexed vectors count: `767`

A CI da branch também passou:

- Ruff: `All checks passed!`
- pytest: `53 passed, 4 warnings`

Conclusão: o pinning reproduz o runtime observado sem alterar a collection existente.
