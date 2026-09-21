import { describe, expect, it } from "vitest"

import { buildChatRequest } from "./chat-api"

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
