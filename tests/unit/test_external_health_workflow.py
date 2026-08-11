from pathlib import Path

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "external-health.yml"


def test_external_health_uses_live_catalog_price() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert 'cron: "17 * * * *"' in source
    assert '"operations"]["url_status"]' in source
    assert 'item["amount"] == expected_amount' in source
    assert 'item["amount"] == "1000"' not in source


def test_external_health_remains_unpaid_and_bounded() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")

    assert 'test "$code" = 402' in source
    assert "PAYMENT-SIGNATURE" not in source
    assert "PAYMENT-PAYLOAD" not in source
    assert "for attempt in 1 2 3" in source
    assert "--connect-timeout 10 --max-time 30" in source
