# Documentos-fonte do RAG

Esta pasta contém os documentos brutos usados pelo pipeline de ingestão.

## Organização

- `alimentacao/`: materiais de alimentação e nutrição.
- `chatscm/`: documentos CHATSCM.
- `diabetes/`: materiais relacionados a diabetes e uso de insulina.
- `direitos_saude/`: direitos e deveres da pessoa usuária da saúde.
- `gestacao/`: materiais gerais de acompanhamento da gestação.
- `medicamentos/`: referências de medicamentos.
- `pessoa_idosa/`: materiais específicos para saúde da pessoa idosa.
- `saude_sexual_reprodutiva/`: contracepção e métodos contraceptivos.
- `vacinacao/`: calendários e materiais de vacinação.

O pipeline deve percorrer estas subpastas recursivamente. A classificação em pastas ajuda na organização humana; a recuperação RAG deverá usar também metadados próprios por documento/chunk.

> Atenção: não versionar documentos com dados pessoais ou clínicos identificáveis. Use somente materiais públicos, sintéticos ou previamente anonimizados.
