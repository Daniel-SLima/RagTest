# Dificuldades TCC

Registro de situações em que uma hipótese, configuração ou decisão planejada não funcionou como esperado na primeira tentativa.

## 1. Filtro de categoria reduziu a qualidade da recuperação

Planejado: restringir a busca a category=vacinacao.

Observado: o filtro excluiu a Caderneta da Pessoa Idosa e piorou os resultados.

Diagnóstico: categoria documental e público-alvo são dimensões diferentes.

Correção: inclusão de audience e filtros por público.

Aprendizado: metadados de domínio influenciam diretamente a precisão do retrieval.

## 2. Limite de saída do Gemini interrompeu a primeira resposta

Planejado: gerar a resposta após recuperar os melhores chunks.

Observado: a primeira resposta terminou após uma frase introdutória.

Diagnóstico: a geração atingiu o limite de tokens.

Correção: aumento do orçamento e retry automático em MAX_TOKENS.

Aprendizado: um RAG pode recuperar corretamente e ainda falhar na etapa de geração.

## 3. Avaliação do retrieval falhou dentro do container

Planejado: executar ragtest-evaluate-retrieval no container.

Observado: FileNotFoundError para tests/evaluation/retrieval_cases.json.

Diagnóstico: o runtime dependia de um arquivo excluído da imagem Docker.

Correção: casos padrão empacotados em app/evaluation/cases.py.

Aprendizado: recursos de runtime não devem depender acidentalmente da estrutura de testes.

## 4. Busca densa não recuperou a carta de direitos e deveres no top 5

Planejado: a pergunta sobre direitos e deveres deveria recuperar direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf.

Observado: na baseline 0.5.1 o documento não apareceu no top 5; medicamentos e caderneta da pessoa idosa ocuparam as primeiras posições.

Diagnóstico: similaridade vetorial densa pode perder correspondências lexicais explícitas presentes no nome do documento.

Correção experimental: reranking por metadados e conteúdo, rank_score separado do score semântico e overfetch ampliado.

Aprendizado: retrieval puramente denso pode falhar em consultas com terminologia exata; a melhoria deve ser comprovada por HitRate e MRR antes/depois.

## Como registrar novos casos

Registrar sempre: planejado, observado, diagnóstico, correção e aprendizado para a monografia.
