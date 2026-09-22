from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_session_defaults_are_bounded_and_local() -> None:
    settings = Settings(_env_file=None)

    assert settings.session_db_path == Path("data/state/sessions.sqlite3")
    assert settings.session_retention_days == 7
    assert settings.session_max_stored_turns == 20
    assert settings.session_context_turns == 6
    assert settings.session_context_max_chars == 12000
    assert settings.session_lease_seconds == 600


def test_release_version_is_0_6_0() -> None:
    assert Settings(_env_file=None).app_version == "0.6.0"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("session_retention_days", 0),
        ("session_context_turns", 21),
        ("session_context_max_chars", 999),
        ("session_lease_seconds", 29),
    ],
)
def test_session_settings_reject_unsafe_bounds(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **{field: value})
