# Dificuldades TCC

Registro de situações em que uma hipótese, configuração ou decisão planejada não funcionou como esperado na primeira tentativa. O objetivo é transformar problemas reais do desenvolvimento em evidências para a análise da monografia.

## 1. Filtro de categoria reduziu a qualidade da recuperação

**Planejado:** restringir a busca a `category=vacinacao` para aumentar a precisão de perguntas sobre vacinas.

**Observado:** sem o filtro, o Qdrant colocou no topo a Caderneta da Pessoa Idosa, página 34, que continha conteúdo diretamente relacionado ao calendário vacinal. Com o filtro por categoria, esse documento foi excluído por pertencer a `pessoa_idosa`, e apareceram resultados de criança e gestante.

**Diagnóstico:** categoria documental e público-alvo representam dimensões diferentes. Um filtro de categoria excessivamente restritivo pode causar perda de informação relevante.

**Correção:** inclusão do metadado `audience` e suporte a filtros como `audience=idoso`, permitindo buscar em categorias diferentes sem misturar públicos.

**Aprendizado para o TCC:** metadados de domínio influenciam diretamente a precisão do retrieval. A modelagem do corpus não deve depender apenas da pasta ou do tema principal do documento.

## 2. Limite de saída do Gemini interrompeu a primeira resposta

**Planejado:** usar o Gemini como etapa de geração após recuperar os melhores chunks.

**Observado:** a primeira resposta terminou após uma frase introdutória porque a geração atingiu o limite de tokens.

**Diagnóstico:** retrieval e contexto estavam corretos; o gargalo estava na configuração de geração do LLM.

**Correção:** aumento do orçamento de saída e retry automático quando o provider retorna `MAX_TOKENS`, com limite maior na segunda tentativa.

**Aprendizado para o TCC:** a camada de geração também exige resiliência. Um RAG pode recuperar evidência corretamente e ainda entregar uma resposta incompleta por limitações operacionais do LLM.

## 3. Avaliação do retrieval falhou dentro do container

**Planejado:** executar `ragtest-evaluate-retrieval` no mesmo container da API usando o conjunto de casos em `tests/evaluation/retrieval_cases.json`.

**Observado:** o comando gerou `FileNotFoundError` porque o arquivo de avaliação não existia dentro da imagem Docker.

**Diagnóstico:** a imagem copiava somente o pacote `app`, enquanto `.dockerignore` excluía o diretório `tests`. O comando de produção dependia indevidamente de um arquivo pertencente à estrutura de testes do repositório.

**Correção:** os casos padrão de avaliação passaram a fazer parte do pacote da aplicação em `app/evaluation/cases.py`. O JSON em `tests/evaluation` continua útil como artefato de teste, mas não é mais uma dependência de runtime. O parâmetro opcional `--cases` continua permitindo avaliar arquivos JSON externos.

**Aprendizado para o TCC:** testes, ferramentas de avaliação e runtime têm ciclos de empacotamento diferentes. Recursos necessários em execução devem ser distribuídos com a aplicação ou montados explicitamente, evitando dependência acidental da estrutura local do repositório.

## Como registrar novos casos

Para cada novo problema relevante, registrar: o que estava planejado, o que foi observado, o diagnóstico técnico, a correção aplicada e o aprendizado que pode ser utilizado na discussão da monografia.
