"""docs/api/openapi.json must match the code, so the published API description never goes stale."""

import json

from app.cli import OPENAPI_OUT
from app.main import create_app


def test_committed_openapi_matches_the_code() -> None:
    committed = json.loads(OPENAPI_OUT.read_text(encoding="utf-8"))
    assert committed == create_app().openapi(), "Run: uv run python -m app.cli export-openapi"
