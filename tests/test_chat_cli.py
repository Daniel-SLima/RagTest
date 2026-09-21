import app.cli.chat as chat_cli
from app.llm.groq_provider import GroqRateLimits


def test_chat_cli_formats_groq_rate_limits_with_explicit_windows() -> None:
    rate_limits = GroqRateLimits(
        limit_requests=1000,
        limit_tokens=8000,
        remaining_requests=987,
        remaining_tokens=6543,
        reset_requests="23h59m",
        reset_tokens="7.66s",
    )

    formatter = getattr(chat_cli, "_format_groq_rate_limits", lambda value: ())

    assert formatter(rate_limits) == (
        "requests_rpd: 987/1000 reset=23h59m",
        "tokens_tpm: 6543/8000 reset=7.66s",
    )
