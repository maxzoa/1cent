import json
from pathlib import Path

from scripts.validate_docs import validate


def test_documentation_is_current_and_linked() -> None:
    validate()


def test_registry_description_respects_official_schema_limit() -> None:
    root = Path(__file__).resolve().parents[2]
    server = json.loads((root / "server.json").read_text(encoding="utf-8"))
    catalog_server = json.loads(
        (root / "catalog" / "server.json").read_text(encoding="utf-8")
    )

    assert 1 <= len(server["description"]) <= 100
    assert catalog_server["description"] == server["description"]
