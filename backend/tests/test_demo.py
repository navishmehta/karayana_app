"""The demo shop command must never touch a production database."""

import pytest

from app.db import demo


def test_seed_demo_refuses_to_run_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    class Production:
        is_production = True

    monkeypatch.setattr(demo, "get_settings", lambda: Production())
    with pytest.raises(demo.DemoError, match="production"):
        demo.build_demo_shop(connection=None)  # type: ignore[arg-type]  # refused before any database access
