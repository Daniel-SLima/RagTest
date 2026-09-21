import { buildChatRequest, sendChatMessage } from "./chat-api"

describe("buildChatRequest", () => {
  it("maps the demo chat input to the FastAPI /v1/chat contract", () => {
    expect(
      buildChatRequest({
        message: "Quais vacinas são recomendadas para idosos?",
        category: "vacinacao",
        audience: "idoso",
      }),
    ).toEqual({
      message: "Quais vacinas são recomendadas para idosos?",
      limit: 5,
      category: "vacinacao",
      audience: "idoso",
      auto_decompose: true,
    })
  })
})


describe("sendChatMessage", () => {
  it("posts the typed request to the FastAPI /v1/chat endpoint", async () => {
    const responseBody = {
      answer: "Vacina recomendada [1].",
      model: "openai/gpt-oss-120b",
      grounded: true,
      citation_ids: [1],
      citation_retry_count: 0,
      multi_query_used: false,
      retrieval_queries: ["Quais vacinas?"],
      decomposition_status: "disabled",
      sources: [
        {
          citation_id: 1,
          score: 0.9,
          source: "vacinacao/calendario.pdf",
          category: "vacinacao",
          audience: "idoso",
          page: 1,
          chunk_count: 1,
          excerpt: "Trecho oficial.",
        },
      ],
    }
    const fetcher = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: jest.fn().mockResolvedValue(responseBody),
    })

    const result = await sendChatMessage(
      {
        message: " Quais vacinas? ",
        category: "vacinacao",
        audience: "idoso",
        minScore: 0.2,
        autoDecompose: false,
      },
      {
        baseUrl: "http://localhost:8000/",
        fetcher,
      },
    )

    expect(fetcher).toHaveBeenCalledWith(
      "http://localhost:8000/v1/chat",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: "Quais vacinas?",
          limit: 5,
          category: "vacinacao",
          audience: "idoso",
          min_score: 0.2,
          auto_decompose: false,
        }),
      },
    )
    expect(result).toEqual(responseBody)
  })
})
