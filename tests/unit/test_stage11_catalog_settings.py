import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from onecent.schemas import ToolRequest, ToolResponse
from onecent.services.settings_registry import PRESETS, SETTING_BY_KEY, SETTINGS
from onecent.services.tool_catalog import TOOL_BY_KEY, TOOL_BY_PATH, TOOLS, public_catalog
from onecent.services.tool_operations import catalog_search


def test_exact_tool_count_and_unique_contracts() -> None:
    assert len(TOOLS) == 43
    assert len(TOOL_BY_KEY) == len(TOOL_BY_PATH) == 43
    assert len({tool.description_en for tool in TOOLS}) == 43
    assert all(tool.price_atomic >= tool.floor_atomic > 0 for tool in TOOLS)
    assert sum(tool.key.startswith("site_") for tool in TOOLS) == 7


def test_public_catalog_has_no_internal_floor_or_audit_fields() -> None:
    rows = public_catalog()
    assert len(rows) == 43
    serialized = json.dumps(rows)
    assert "floor_atomic" not in serialized
    assert "updated_by" not in serialized


def test_strict_projection_schemas() -> None:
    with pytest.raises(ValidationError):
        ToolRequest.model_validate({"url": "https://example.com", "unknown": True})
    schema = ToolResponse.model_json_schema()
    assert schema["additionalProperties"] is False


def test_free_catalog_search_is_local_and_bounded() -> None:
    rows = catalog_search("redirect chain")
    assert 1 <= len(rows) <= 5
    assert rows[0]["tool"] == "url_redirects"


def test_settings_visibility_editability_and_locked_gates() -> None:
    assert len(SETTINGS) >= 45
    assert sum(setting.editable for setting in SETTINGS) >= 30
    for key in (
        "network",
        "facilitator",
        "seller",
        "ssrf_protection",
        "payment_verification",
        "automatic_rollback",
    ):
        item = SETTING_BY_KEY[key]
        assert item.editable is False
        assert item.risk == "locked"
    assert set(PRESETS) == {"safe", "balanced", "growth"}
    for values in PRESETS.values():
        assert not {"network", "facilitator", "seller", "automatic_rollback"} & values.keys()


def test_selection_benchmark_has_required_mix() -> None:
    path = Path(__file__).parents[2] / "benchmark" / "tool_selection_cases.json"
    cases = json.loads(path.read_text(encoding="utf-8"))
    assert len(cases) >= 100
    kinds = {case["kind"] for case in cases}
    assert kinds == {"clear", "conflict", "negative"}
