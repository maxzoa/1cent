from datetime import datetime, timedelta, timezone
from pathlib import Path

from onecent.config import Settings
from onecent.services.costs import cost_breakdown
from onecent.services.readiness import backup_age_hours, mainnet_blockers


def test_testnet_is_not_mainnet_ready() -> None:
    blockers = mainnet_blockers(Settings(_env_file=None))
    assert "OWNER_MAINNET_APPROVED is not true" in blockers
    assert "X402_NETWORK is not eip155:8453" in blockers


def test_backup_age(tmp_path: Path) -> None:
    backup = tmp_path / "backup.dump"
    backup.write_bytes(b"backup")
    now = datetime.now(timezone.utc) + timedelta(hours=2)
    age = backup_age_hours(str(backup), now)
    assert age is not None
    assert 1.9 < age < 2.1


def test_cost_floor_and_margin() -> None:
    costs = cost_breakdown(Settings(_env_file=None), "pulse", "0.003000")
    assert costs["minimum_safe_price"] == costs["margin_cache_miss"] + costs["cache_miss_cost"]
    assert costs["minimum_safe_price"] == costs["margin_cache_hit"] + costs["cache_hit_cost"]
    assert costs["margin_cache_miss"] == costs["margin_cache_hit"] - costs["fetch_miss"]
