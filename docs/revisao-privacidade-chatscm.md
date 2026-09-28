# Revisão de privacidade — CHATSCM

Objetivo: decidir se `data/source/chatscm/*.docx` (FAQ do Se Cuida Mulher) pode ser enviado a
providers externos (Gemini/Groq). Enquanto a decisão D038 não for aprovada, a regra antiga do
`AGENTS.md` continua valendo.

## 1. Auditoria automática — 2026-09-28

Comando:

    ragtest-audit-pii --subdir chatscm

Resultado (somente metadados, sem imprimir texto):

| Arquivo | Parágrafos | Achados |
|---|---|---|
| chatscm.docx | 210 | 0 |
| chatscm_gestante.docx | 117 | 0 |
| chatscm_gestante_parte_2.docx | 77 | 0 |

Categorias verificadas: CPF, CNPJ, Cartão SUS (CNS), telefone, e-mail, CEP e datas.

## 2. Checklist manual (a ser preenchido pelo autor)

- [ ] Não há nomes de pacientes ou de pessoas físicas identificáveis.
- [ ] Não há endereços residenciais.
- [ ] Não há relatos de casos clínicos individuais.
- [ ] O conteúdo é orientação institucional genérica (FAQ).
- [ ] Nomes de unidades de saúde/profissionais, se existirem, são públicos e institucionais.

## 3. Decisão

Se todos os itens forem marcados, mudar a D038 para **Aprovada** em `docs/decisoes-tecnicas.md`,
remover a restrição correspondente do `AGENTS.md` e registrar a data aqui.

- Status: **aguardando revisão manual do autor**
