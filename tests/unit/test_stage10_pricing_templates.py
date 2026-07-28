from decimal import Decimal
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

from onecent.config import Settings
from onecent.services.costs import atomic_to_usd, cost_breakdown, usd_to_atomic
from onecent.services.message_templates import validate_template


def _migration_templates() -> dict[str, tuple[str, list[str]]]:
    path = Path(__file__).parents[2] / "migrations/versions/0003_pricing_and_telegram_templates.py"
    spec = spec_from_file_location("stage10_migration", path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.TEMPLATES


def test_decimal_atomic_conversion_is_exact() -> None:
    assert usd_to_atomic("0.003000") == 3000
    assert usd_to_atomic("0.010000") == 10000
    assert atomic_to_usd(3000) == Decimal("0.003000")
    with pytest.raises(ValueError):
        usd_to_atomic("0.0000001")


def test_new_prices_pass_floor_and_have_positive_margin() -> None:
    settings = Settings(_env_file=None)
    for operation, price in {
        "pulse": "0.003000",
        "passport": "0.010000",
        "extract": "0.010000",
        "changed": "0.003000",
    }.items():
        costs = cost_breakdown(settings, operation, price)
        assert Decimal(price) >= costs["minimum_safe_price"]
        assert costs["margin_cache_hit"] > 0
        assert costs["margin_cache_miss"] > 0


def test_template_seed_count_keys_and_placeholders() -> None:
    templates = _migration_templates()
    assert len(templates) >= 32
    assert sum(len(value[1]) for value in templates.values()) >= 60
    for event_key, (_, variants) in templates.items():
        for template in variants:
            validate_template(event_key, template)


def test_unknown_placeholder_rejected() -> None:
    with pytest.raises(ValueError, match="unknown placeholders"):
        validate_template("status_ok", "{secret}")


def test_registry_metadata_has_no_price_so_no_republish() -> None:
    text = (Path(__file__).parents[2] / "server.json").read_text(encoding="utf-8")
    assert "0.01" not in text
    assert "price" not in text.lower()
