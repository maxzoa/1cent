from decimal import Decimal
from typing import Protocol


class CostSettings(Protocol):
    cost_facilitator_fee_usd: str
    cost_rpc_usd: str
    cost_fetch_usd: str
    cost_margin_target_usd: str
    price_floor_pulse_usd: str
    price_floor_passport_usd: str
    price_floor_extract_usd: str
    price_floor_changed_usd: str


def cost_breakdown(settings: CostSettings, operation: str, price: str) -> dict[str, Decimal]:
    facilitator = Decimal(settings.cost_facilitator_fee_usd)
    rpc = Decimal(settings.cost_rpc_usd)
    fetch = Decimal(settings.cost_fetch_usd)
    margin_target = Decimal(settings.cost_margin_target_usd)
    configured_floor = Decimal(getattr(settings, f"price_floor_{operation}_usd"))
    miss_cost = facilitator + rpc + fetch
    hit_cost = facilitator + rpc
    safe_floor = max(configured_floor, miss_cost + margin_target)
    value = Decimal(price)
    return {
        "facilitator_fee": facilitator,
        "rpc": rpc,
        "fetch_miss": fetch,
        "cache_hit_cost": hit_cost,
        "cache_miss_cost": miss_cost,
        "margin_cache_hit": value - hit_cost,
        "margin_cache_miss": value - miss_cost,
        "minimum_safe_price": safe_floor,
    }


USDC_SCALE = Decimal("1000000")


def usd_to_atomic(value: str | Decimal) -> int:
    decimal_value = Decimal(value)
    atomic = decimal_value * USDC_SCALE
    if decimal_value <= 0 or atomic != atomic.to_integral_value():
        raise ValueError("USDC price must be positive with at most 6 decimals")
    return int(atomic)


def atomic_to_usd(value: int) -> Decimal:
    if value <= 0:
        raise ValueError("atomic amount must be positive")
    return (Decimal(value) / USDC_SCALE).quantize(Decimal("0.000001"))
