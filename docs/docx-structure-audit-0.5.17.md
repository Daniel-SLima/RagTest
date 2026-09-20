# Auditoria estrutural dos DOCX — RagTest 0.5.17

Data: 2026-09-20

Objetivo: verificar se os DOCX do corpus contêm conteúdo estrutural relevante fora de `document.paragraphs` antes de alterar o loader.

A auditoria foi deliberadamente metadata-only: nenhum conteúdo textual dos arquivos foi impresso.

## Resultado

### chatscm/chatscm.docx

- parágrafos do corpo: 208 total / 145 não vazios
- tabelas do corpo: 0
- linhas de tabela: 0
- células de tabela: 0
- células não vazias: 0
- seções: 1
- parágrafos de cabeçalho: 1 total / 0 não vazios
- tabelas de cabeçalho: 0
- parágrafos de rodapé: 1 total / 0 não vazios
- tabelas de rodapé: 0
- conteúdo estrutural fora dos parágrafos do corpo: não

### chatscm/chatscm_gestante.docx

- parágrafos do corpo: 115 total / 89 não vazios
- tabelas do corpo: 0
- linhas de tabela: 0
- células de tabela: 0
- células não vazias: 0
- seções: 1
- parágrafos de cabeçalho: 1 total / 0 não vazios
- tabelas de cabeçalho: 0
- parágrafos de rodapé: 1 total / 0 não vazios
- tabelas de rodapé: 0
- conteúdo estrutural fora dos parágrafos do corpo: não

### chatscm/chatscm_gestante_parte_2.docx

- parágrafos do corpo: 75 total / 53 não vazios
- tabelas do corpo: 0
- linhas de tabela: 0
- células de tabela: 0
- células não vazias: 0
- seções: 1
- parágrafos de cabeçalho: 1 total / 0 não vazios
- tabelas de cabeçalho: 0
- parágrafos de rodapé: 1 total / 0 não vazios
- tabelas de rodapé: 0
- conteúdo estrutural fora dos parágrafos do corpo: não

## Conclusão

Os três DOCX atuais não possuem tabelas nem conteúdo não vazio em cabeçalhos/rodapés. Portanto, ampliar o loader para esses elementos não traria ganho para o corpus atual e mudaria código sem necessidade observada.

A decisão da 0.5.17 é manter o loader DOCX atual para esses elementos e preservar os 767 chunks já validados.

Esta auditoria não substitui uma revisão manual de privacidade dos arquivos CHATSCM e não afirma que eles estejam anonimizados.
