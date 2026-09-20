EVALUATION_DATASET_VERSION = "2026-09-20-v1"


DEV_RETRIEVAL_CASES: list[dict[str, object]] = [
    {
        "id": "dev-vacinas-idoso",
        "query": "Quais vacinas são recomendadas para idosos?",
        "audience": "idoso",
        "expected_sources": [
            "vacinacao/calendario_nacional_vacinacao_idoso.pdf",
            "pessoa_idosa/caderneta_saude_pessoa_idosa_5ed_1re.pdf",
        ],
    },
    {
        "id": "dev-vacinas-gestacao",
        "query": "Quais vacinas são indicadas durante a gestação?",
        "audience": "gestante",
        "expected_sources": [
            "vacinacao/calendario_nacional_vacinacao_gestante.pdf",
            "gestacao/caderneta_gestante_8ed_rev.pdf",
        ],
    },
    {
        "id": "dev-vacinas-crianca",
        "query": "Quais vacinas fazem parte do calendário da criança?",
        "audience": "crianca",
        "expected_sources": [
            "vacinacao/calendario_nacional_vacinacao_crianca.pdf",
        ],
    },
    {
        "id": "dev-diu",
        "query": "Quais informações existem sobre o DIU de cobre?",
        "expected_sources": [
            "saude_sexual_reprodutiva/diu_cobre_ministerio_saude.pdf",
        ],
    },
    {
        "id": "dev-implante",
        "query": "Quais informações existem sobre o implante contraceptivo?",
        "expected_sources": [
            "saude_sexual_reprodutiva/implante_ministerio_saude.pdf",
        ],
    },
    {
        "id": "dev-insulina",
        "query": "Como utilizar canetas aplicadoras de insulina?",
        "expected_sources": [
            "diabetes/cartilha_canetas_insulina_pacientes.pdf",
        ],
    },
    {
        "id": "dev-direitos",
        "query": "Quais são os direitos e deveres da pessoa usuária da saúde?",
        "expected_sources": [
            "direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf",
        ],
    },
]


HOLDOUT_RETRIEVAL_CASES: list[dict[str, object]] = [
    {
        "id": "holdout-alimentacao-saudavel",
        "query": "O que significa ter uma alimentação adequada e saudável no dia a dia?",
        "expected_sources": [
            "alimentacao/guia_alimentar_populacao_brasileira_resumido.pdf",
        ],
    },
    {
        "id": "holdout-vacinas-adulto",
        "query": "Quais vacinas uma pessoa adulta deve manter em dia?",
        "audience": "adulto",
        "expected_sources": [
            "vacinacao/calendario_nacional_vacinacao_adulto.pdf",
        ],
    },
    {
        "id": "holdout-vacinas-adolescente",
        "query": "Quais vacinas são indicadas para adolescentes e jovens?",
        "audience": "adolescente_jovem",
        "expected_sources": [
            "vacinacao/calendario_nacional_vacinacao_adolescentes_jovens.pdf",
        ],
    },
    {
        "id": "holdout-saude-bucal-gestante",
        "query": "Quais cuidados de saúde bucal são recomendados durante a gestação?",
        "audience": "gestante",
        "expected_sources": [
            "gestacao/cartilha_saude_bucal_gestante.pdf",
        ],
    },
    {
        "id": "holdout-caderneta-gestante",
        "query": "Que orientações a caderneta da gestante traz sobre o pré-natal?",
        "audience": "gestante",
        "expected_sources": [
            "gestacao/caderneta_gestante_8ed_rev.pdf",
        ],
    },
    {
        "id": "holdout-caderneta-idoso",
        "query": "Que informações de saúde e acompanhamento aparecem na caderneta da pessoa idosa?",
        "audience": "idoso",
        "expected_sources": [
            "pessoa_idosa/caderneta_saude_pessoa_idosa_5ed_1re.pdf",
        ],
    },
    {
        "id": "holdout-rename-2024",
        "query": "Onde consultar a Relação Nacional de Medicamentos Essenciais de 2024?",
        "expected_sources": [
            "medicamentos/relacao_nacional_medicamentos_2024.pdf",
        ],
    },
    {
        "id": "holdout-contracepcao-ampla",
        "query": "Quais métodos contraceptivos são apresentados pelo Ministério da Saúde?",
        "expected_sources": [
            "saude_sexual_reprodutiva/contracepcao_ministerio_saude.pdf",
            "saude_sexual_reprodutiva/diu_cobre_ministerio_saude.pdf",
            "saude_sexual_reprodutiva/implante_ministerio_saude.pdf",
        ],
    },
    {
        "id": "holdout-diu-parafrase",
        "query": "Quero saber sobre o anticoncepcional intrauterino de cobre.",
        "expected_sources": [
            "saude_sexual_reprodutiva/diu_cobre_ministerio_saude.pdf",
        ],
    },
    {
        "id": "holdout-insulina-parafrase",
        "query": "Como aplicar insulina usando caneta?",
        "expected_sources": [
            "diabetes/cartilha_canetas_insulina_pacientes.pdf",
        ],
    },
    {
        "id": "holdout-direitos-parafrase",
        "query": "Quais garantias e responsabilidades tenho ao usar os serviços de saúde?",
        "expected_sources": [
            "direitos_saude/carta_direitos_deveres_pessoa_usuaria_saude.pdf",
        ],
    },
    {
        "id": "holdout-vacinas-crianca-parafrase",
        "query": "Meu filho precisa tomar quais vacinas do calendário nacional?",
        "audience": "crianca",
        "expected_sources": [
            "vacinacao/calendario_nacional_vacinacao_crianca.pdf",
        ],
    },
    {
        "id": "holdout-vacinas-idoso-parafrase",
        "query": "Quais imunizações devem estar em dia depois dos 60 anos?",
        "audience": "idoso",
        "expected_sources": [
            "vacinacao/calendario_nacional_vacinacao_idoso.pdf",
            "pessoa_idosa/caderneta_saude_pessoa_idosa_5ed_1re.pdf",
        ],
    },
    {
        "id": "holdout-vacinas-gestante-parafrase",
        "query": "Na gravidez, quais imunizações devo manter atualizadas?",
        "audience": "gestante",
        "expected_sources": [
            "vacinacao/calendario_nacional_vacinacao_gestante.pdf",
            "gestacao/caderneta_gestante_8ed_rev.pdf",
        ],
    },
    {
        "id": "holdout-implante-parafrase",
        "query": "Como funciona o implante hormonal contraceptivo?",
        "expected_sources": [
            "saude_sexual_reprodutiva/implante_ministerio_saude.pdf",
        ],
    },
]


DEFAULT_RETRIEVAL_CASES = DEV_RETRIEVAL_CASES


def select_retrieval_cases(suite: str) -> list[dict[str, object]]:
    if suite == "dev":
        return [dict(case) for case in DEV_RETRIEVAL_CASES]
    if suite == "holdout":
        return [dict(case) for case in HOLDOUT_RETRIEVAL_CASES]
    if suite == "all":
        return [
            *(dict(case) for case in DEV_RETRIEVAL_CASES),
            *(dict(case) for case in HOLDOUT_RETRIEVAL_CASES),
        ]
    raise ValueError(f"Unsupported evaluation suite: {suite}")
