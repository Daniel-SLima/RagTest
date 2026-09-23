import type {
  RoadmapCounts,
  RoadmapFilter,
  RoadmapItem,
  RoadmapSnapshot,
  RoadmapStatus,
} from "../types/roadmap"

export const ROADMAP_SNAPSHOT: RoadmapSnapshot = {
  branch: "sidequest/ragtest-demo",
  commit: "75c924c",
  version: "M5",
  date: "2026-09-23",
}

export const ROADMAP_STATUSES: readonly RoadmapStatus[] = ["implemented", "partial", "planned", "research"]

const item = (
  value: Omit<RoadmapItem, "snapshotCommit">,
): RoadmapItem => ({ ...value, snapshotCommit: ROADMAP_SNAPSHOT.commit })

export const ROADMAP_ITEMS: readonly RoadmapItem[] = [
  item({
    id: "rag-api",
    area: "Núcleo RAG e API",
    title: "Núcleo RAG e API REST",
    status: "implemented",
    simpleExplanation: "O módulo recebe perguntas, recupera documentos e expõe respostas por uma API reutilizável.",
    technicalExplanation: "FastAPI coordena o pipeline RAG com retrieval documental e providers explícitos, mantendo o backend independente do Expo.",
    whyItMatters: "Uma fronteira HTTP estável permite integrar o módulo a clientes diferentes.",
    dependencies: [],
    evidence: [
      { kind: "source", reference: "README.md:15-46", label: "Contrato REST e execução local documentados" },
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:344-405", label: "Arquitetura atual do módulo" },
    ],
    origin: "README.md e docs/CONTEXTO_CONTINUIDADE.md",
    snapshotVersion: "M1",
  }),
  item({
    id: "retrieval-evaluation",
    area: "Retrieval e avaliação",
    title: "Retrieval e avaliação documental",
    status: "implemented",
    simpleExplanation: "Há recuperação híbrida e uma avaliação versionada para medir a qualidade dos documentos encontrados.",
    technicalExplanation: "O projeto preserva métricas HitRate/MRR e métricas em nível de fonte para conjuntos dev e holdout, sem ajustar o corpus durante a avaliação.",
    whyItMatters: "Medir retrieval separadamente reduz o risco de atribuir ao gerador uma falha de busca.",
    dependencies: ["rag-api"],
    evidence: [
      { kind: "source", reference: "README.md:48-122", label: "Avaliação dev/holdout e métricas documentadas" },
      { kind: "document", reference: "docs/decisoes-tecnicas.md:69-75", label: "Decisão de avaliação holdout" },
    ],
    origin: "README.md e docs/decisoes-tecnicas.md",
    snapshotVersion: "M1",
  }),
  item({
    id: "structural-grounding",
    area: "Grounding estrutural",
    title: "Citações e gate de grounding",
    status: "implemented",
    simpleExplanation: "A resposta pode mostrar as fontes citadas e distingue cobertura estrutural de verdade clínica.",
    technicalExplanation: "O cliente correlaciona citation_ids com sources; o gate valida cobertura de citações e mantém fallback seguro quando ela não é suficiente.",
    whyItMatters: "A usuária precisa saber quando há uma base documental apresentada, sem receber uma promessa de garantia factual.",
    dependencies: ["rag-api", "retrieval-evaluation"],
    evidence: [
      { kind: "document", reference: "README.md:630-670", label: "Grounding estrutural e fontes citadas" },
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:1000-1015", label: "Gate de cobertura registrado" },
    ],
    origin: "README.md e docs/CONTEXTO_CONTINUIDADE.md",
    snapshotVersion: "M1",
  }),
  item({
    id: "demo-chat",
    area: "Demo Expo",
    title: "Chat demonstrativo no Expo",
    status: "implemented",
    simpleExplanation: "A demo apresenta o fluxo de pergunta, resposta, fontes, loading e erro sem se passar pelo produto final.",
    technicalExplanation: "O cliente Expo valida DTOs fechados, usa chamadas explícitas e mantém o runtime controlado por flags independentes.",
    whyItMatters: "Uma superfície demonstrativa torna o comportamento do módulo observável durante a avaliação.",
    dependencies: ["rag-api", "structural-grounding"],
    evidence: [
      { kind: "test", reference: "frontend/src/demo/screens/demo-screens.test.tsx", label: "Testes de estados e limites da demo" },
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:196-249", label: "Validação M3 do cliente Expo" },
    ],
    origin: "frontend/src/demo e docs/CONTEXTO_CONTINUIDADE.md",
    snapshotVersion: "M2",
  }),
  item({
    id: "laboratory-m4",
    area: "Laboratório experimental",
    title: "Laboratório de comparação de retrieval",
    status: "planned",
    simpleExplanation: "A demo reserva uma área para comparar estratégias, mas essa execução ainda não faz parte do produto verificado.",
    technicalExplanation: "O plano M4 descreve Dense, Dense+rerank, Hybrid, Top K e multi-query como controles futuros sujeitos a contratos e segurança próprios.",
    whyItMatters: "Comparações reproduzíveis ajudam a explicar o efeito de estratégias de retrieval.",
    whyMissing: "A fronteira M4 continua planejada e não autoriza novas chamadas ou expansão do backend nesta versão.",
    dependencies: ["retrieval-evaluation", "production-security"],
    evidence: [
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:241-245", label: "Próxima fronteira M4 documentada" },
      { kind: "document", reference: "docs/superpowers/plans/2026-09-23-ragtest-demo-m4.md:16-18", label: "Limites do plano M4" },
    ],
    origin: "docs/CONTEXTO_CONTINUIDADE.md e docs/superpowers/plans/2026-09-23-ragtest-demo-m4.md",
    snapshotVersion: "M2",
  }),
  item({
    id: "backend-sessions",
    area: "Sessões e contexto",
    title: "Sessões conversacionais no backend",
    status: "partial",
    simpleExplanation: "O backend possui ciclo de vida e contexto de sessão, mas o cliente Expo ainda não integra essa identidade.",
    technicalExplanation: "A especificação 0.6.0 define SessionStore, expiração, histórico limitado e lease por sessão; a integração de sessão no Expo está fora do recorte.",
    whyItMatters: "Sessões permitem contexto controlado sem misturar histórico com evidência documental.",
    whyMissing: "Autenticação, identidade do aplicativo e uma experiência de sessão no cliente exigem decisões e validações próprias.",
    dependencies: ["rag-api"],
    evidence: [
      { kind: "document", reference: "docs/superpowers/specs/2026-09-21-sessoes-conversacionais-0.6.0-design.md:77-169", label: "Design de sessões portáveis" },
      { kind: "document", reference: "docs/decisoes-tecnicas.md:305-319", label: "Decisão backend-first para sessões" },
    ],
    origin: "docs/superpowers/specs e docs/decisoes-tecnicas.md",
    snapshotVersion: "M2",
  }),
  item({
    id: "document-base",
    area: "Base documental e sincronização",
    title: "Base documental versionada",
    status: "implemented",
    simpleExplanation: "O núcleo usa uma base documental validada e mantém ingestão, embeddings e coleção vetorial fora do cliente.",
    technicalExplanation: "O corpus atual tem 18 arquivos e 767 pontos; mudanças de fonte seguem dry-run e revisão antes de sincronização.",
    whyItMatters: "A rastreabilidade da fonte é necessária para avaliar retrieval e contextualizar respostas.",
    dependencies: ["retrieval-evaluation"],
    evidence: [
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:575-586", label: "Corpus e avaliação registrados" },
      { kind: "document", reference: "docs/PROMPT_RETOMADA.md:102-116", label: "Regras de sincronização documental" },
    ],
    origin: "docs/CONTEXTO_CONTINUIDADE.md e docs/PROMPT_RETOMADA.md",
    snapshotVersion: "M1",
  }),
  item({
    id: "production-security",
    area: "Segurança e produção",
    title: "Proteções para uso externo",
    status: "partial",
    simpleExplanation: "Há validações e limites locais, mas a demo ainda não está pronta para uso externo ou produção.",
    technicalExplanation: "A revisão registra ausência de autenticação e rate limiting, logs preexistentes que precisam de saneamento e risco residual de prompt injection.",
    whyItMatters: "Uma demonstração local não deve ser confundida com um serviço seguro para dados reais.",
    whyMissing: "O endurecimento para produção requer revisão operacional, controle de acesso, limites e observabilidade próprios.",
    dependencies: ["rag-api"],
    evidence: [
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:297-306", label: "Bloqueios de uso externo registrados" },
      { kind: "document", reference: "docs/demo-m1.md:250-265", label: "Limitações de segurança da demo" },
    ],
    origin: "docs/CONTEXTO_CONTINUIDADE.md e docs/demo-m1.md",
    snapshotVersion: "M2",
  }),
  item({
    id: "privacy-lgpd",
    area: "Privacidade e LGPD",
    title: "Privacidade e uso responsável em saúde",
    status: "research",
    simpleExplanation: "Privacidade, dados pessoais e limites clínicos continuam sendo uma frente de revisão, não uma certificação pronta.",
    technicalExplanation: "O projeto exige revisão manual antes de enviar conteúdo privado a providers e explicita que grounding estrutural não prova segurança clínica ou entailment.",
    whyItMatters: "O domínio de saúde exige separar evidência técnica de autorização, política clínica e proteção de dados.",
    whyMissing: "Ainda é necessária uma avaliação especializada de privacidade, LGPD, política clínica e operação com dados reais.",
    dependencies: ["production-security", "document-base"],
    evidence: [
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:226-239", label: "Limites de privacidade e operação local" },
      { kind: "document", reference: "docs/decisoes-tecnicas.md:305-307", label: "Separação entre módulo e aplicativo" },
    ],
    origin: "docs/CONTEXTO_CONTINUIDADE.md e docs/decisoes-tecnicas.md",
    snapshotVersion: "M2",
  }),
  item({
    id: "specialized-evaluation",
    area: "Avaliação especializada e usabilidade",
    title: "Avaliação especializada e usabilidade",
    status: "research",
    simpleExplanation: "Métricas técnicas existem, mas avaliação com especialistas, usuárias e cenários de uso ainda precisa ser definida.",
    technicalExplanation: "O histórico prioriza métricas de retrieval e mantém avaliação/usabilidade como etapa futura, sem transformar observação visual em evidência clínica.",
    whyItMatters: "Qualidade de busca não substitui adequação linguística, usabilidade ou revisão especializada em saúde.",
    whyMissing: "Faltam protocolo aprovado, participantes, critérios especializados e validação ética/operacional para essa frente.",
    dependencies: ["retrieval-evaluation", "privacy-lgpd"],
    evidence: [
      { kind: "document", reference: "README.md:118-122", label: "Evolução das métricas de avaliação" },
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:2050-2058", label: "Avaliação e usabilidade como etapa futura" },
    ],
    origin: "README.md e docs/CONTEXTO_CONTINUIDADE.md",
    snapshotVersion: "M2",
  }),
  item({
    id: "se-cuida-integration",
    area: "Integração Se Cuida Mulher",
    title: "Integração futura ao Se Cuida Mulher",
    status: "planned",
    simpleExplanation: "O módulo foi desenhado para ser integrável, mas ainda não é a integração oficial do aplicativo.",
    technicalExplanation: "A arquitetura mantém o backend desacoplado do Expo; identidade, fluxos institucionais e ações do aplicativo dependem do sistema integrador.",
    whyItMatters: "A integração é o destino de produto documentado para o módulo do TCC.",
    whyMissing: "Não há acesso ao aplicativo final nem decisão aprovada sobre identidade, agendamento, links ou notificações.",
    dependencies: ["rag-api", "backend-sessions", "production-security", "privacy-lgpd"],
    evidence: [
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:344-361", label: "Objetivo de integração documentado" },
      { kind: "document", reference: "README.md:1-24", label: "Módulo portável e cliente demonstrativo" },
    ],
    origin: "docs/CONTEXTO_CONTINUIDADE.md e README.md",
    snapshotVersion: "M2",
  }),
  item({
    id: "audit-observability",
    area: "Auditoria e observabilidade",
    title: "Auditoria estruturada e observabilidade",
    status: "planned",
    simpleExplanation: "Há uma especificação para eventos sanitizados, mas sua implementação funcional está fora deste catálogo executado.",
    technicalExplanation: "O design 0.7.0-A define eventos sem perguntas, respostas, prompts ou excerpts, mantendo o sink desacoplado do fluxo principal.",
    whyItMatters: "Auditoria limitada e sanitizada favorece diagnóstico sem transformar conteúdo de saúde em log.",
    whyMissing: "A implementação e sua validação ainda aguardam retomada autorizada da versão 0.7.0-A.",
    dependencies: ["production-security", "backend-sessions"],
    evidence: [
      { kind: "document", reference: "docs/superpowers/specs/2026-09-22-auditoria-estruturada-0.7.0-a-design.md:90-148", label: "Design de auditoria estruturada" },
      { kind: "document", reference: "docs/CONTEXTO_CONTINUIDADE.md:35-38", label: "Implementação da auditoria pausada" },
    ],
    origin: "docs/superpowers/specs e docs/CONTEXTO_CONTINUIDADE.md",
    snapshotVersion: "M2",
  }),
]

export const ROADMAP_AREAS: readonly string[] = [...new Set(ROADMAP_ITEMS.map((roadmapItem) => roadmapItem.area))]

export function validateRoadmapItems(items: readonly RoadmapItem[]): void {
  const ids = new Set<string>()
  for (const roadmapItem of items) {
    if (ids.has(roadmapItem.id)) throw new Error(`Roadmap item id duplicated: ${roadmapItem.id}`)
    ids.add(roadmapItem.id)
    if (!ROADMAP_STATUSES.includes(roadmapItem.status)) throw new Error(`Unknown roadmap status: ${roadmapItem.status}`)
    if (roadmapItem.evidence.length === 0) throw new Error(`Roadmap item has no evidence: ${roadmapItem.id}`)
  }
  for (const roadmapItem of items) {
    for (const dependency of roadmapItem.dependencies) {
      if (!ids.has(dependency)) throw new Error(`Roadmap dependency not found: ${roadmapItem.id} -> ${dependency}`)
    }
  }
}

validateRoadmapItems(ROADMAP_ITEMS)

export function getRoadmapCounts(items: readonly RoadmapItem[]): RoadmapCounts {
  const byStatus = Object.fromEntries(ROADMAP_STATUSES.map((status) => [status, 0])) as Record<RoadmapStatus, number>
  const byArea: Record<string, number> = {}
  for (const roadmapItem of items) {
    byStatus[roadmapItem.status] += 1
    byArea[roadmapItem.area] = (byArea[roadmapItem.area] ?? 0) + 1
  }
  return { byStatus, byArea }
}

export function filterRoadmapItems(items: readonly RoadmapItem[], filters: RoadmapFilter = {}): RoadmapItem[] {
  const status = filters.status ?? "all"
  const area = filters.area ?? "all"
  return items.filter((roadmapItem) => {
    const matchesStatus = status === "all" || roadmapItem.status === status
    const matchesArea = area === "all" || roadmapItem.area === area
    return matchesStatus && matchesArea
  })
}

// Backward-compatible name used by the M2 screen until the M5 screen consumes ROADMAP_ITEMS directly.
export const roadmap = ROADMAP_ITEMS
