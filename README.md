# RagTest

Módulo RAG reutilizável via API.

## Estado experimental

Resultados medidos:

    0.5.1  HitRate@5=0.857  MRR@5=0.714
    0.5.2  HitRate@5=0.857  MRR@5=0.786
    0.5.3  HitRate@5=0.714  MRR@5=0.607
    0.5.4  HitRate@5=0.857  MRR@5=0.690

A 0.5.2 continua sendo o melhor resultado medido. A 0.5.5 não tenta melhorar ranking: ela audita a cobertura do corpus para descobrir por que uma fonte específica nunca aparece.

## Auditoria de extração

Atualize:

    git pull origin main
    docker compose down
    docker compose up --build -d

Depois rode apenas para a categoria problemática:

    docker compose run --rm api ragtest-inspect --source direitos_saude

Ou para todo o corpus:

    docker compose run --rm api ragtest-inspect

A tabela mostra unidades carregadas, unidades com texto, caracteres extraídos, chunks e status.

Não é necessário reindexar para executar essa auditoria.

## Dificuldades TCC

Registro contínuo em docs/dificuldades-tcc.md.

## Segurança

Nunca versione GEMINI_API_KEY. Use apenas .env local.
