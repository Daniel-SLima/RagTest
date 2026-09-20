import asyncio

from app.rag.decomposition import (
    decompose_question,
    parse_subqueries,
    should_attempt_decomposition,
)


class FakePlanner:
    model_name = "fake-planner"

    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    async def generate(self, *, system_prompt: str, user_prompt: str) -> str:
        self.calls += 1
        return self.response


async def run() -> None:
    compound = "Quais são os direitos e deveres da pessoa usuária da saúde?"
    simple = "Quais vacinas são recomendadas para idosos?"

    planner = FakePlanner(
        '{"subqueries":["Quais são os direitos da pessoa usuária da saúde?",'
        '"Quais são os deveres da pessoa usuária da saúde?"]}'
    )
    result = await decompose_question(compound, llm=planner)

    simple_planner = FakePlanner('{"subqueries":["não deveria ser chamado"]}')
    simple_result = await decompose_question(simple, llm=simple_planner)

    checks = [
        ("compound question reaches planner", planner.calls == 1),
        ("compound question becomes multi-query", result.used),
        ("two subqueries preserved", len(result.subqueries) == 2),
        (
            "simple question skips planner",
            simple_planner.calls == 0 and not simple_result.attempted,
        ),
        (
            "malformed planner output falls back safely",
            parse_subqueries("não é json", compound) == (),
        ),
        (
            "compound heuristic detects coordinated intent",
            should_attempt_decomposition(compound),
        ),
    ]

    print("RagTest automatic decomposition self-check")
    failed = 0
    for name, passed in checks:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}")
        if not passed:
            failed += 1

    if failed:
        raise SystemExit(f"{failed} decomposition self-check(s) failed")

    print("All automatic decomposition self-checks passed.")


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
