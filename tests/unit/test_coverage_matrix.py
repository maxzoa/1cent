import json
from pathlib import Path


def test_coverage_matrix_has_no_unknown_and_explicit_surface_decisions() -> None:
    root = Path(__file__).resolve().parents[2]
    payload = json.loads((root / "WEB_INTELLIGENCE_COVERAGE_MATRIX.json").read_text("utf-8"))
    rows = payload["capabilities"]
    assert payload["summary"]["unknown"] == 0
    assert payload["summary"]["total"] == len(rows) == 26
    assert len({row["id"] for row in rows}) == len(rows)
    for row in rows:
        assert row["status"] in {
            "implemented",
            "planned",
            "blocked_external",
            "unsafe",
            "no_demand",
        }
        assert row["rest_status"]
        assert row["remote_mcp_status"]
        assert row["buyer_bridge_status"]
        assert row["pricing_contract"]
        assert row["reason"]
        assert row["evidence"].startswith("https://")
        assert row["review_date"]
