from __future__ import annotations

import asyncio
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from onecent.config import Settings
from onecent.repositories.payments import operation_price, set_operation_price
from onecent.services.costs import cost_breakdown, usd_to_atomic

OPERATIONS = ("pulse", "passport", "extract", "changed")


class PricingRegistry:
    def __init__(self) -> None:
        self._cache: dict[str, Decimal] = {}
        self._lock = asyncio.Lock()

    async def get(self, session: AsyncSession, operation: str, settings: Settings) -> Decimal:
        if operation not in OPERATIONS:
            raise ValueError("unknown operation")
        if operation in self._cache:
            return self._cache[operation]
        async with self._lock:
            default = getattr(settings, f"price_{operation}_usd")
            value = Decimal(await operation_price(session, operation, default))
            usd_to_atomic(value)
            self._cache[operation] = value
            return value

    def invalidate(self, operation: str | None = None) -> None:
        if operation is None:
            self._cache.clear()
        else:
            self._cache.pop(operation, None)

    async def update(
        self,
        session: AsyncSession,
        operation: str,
        value: Decimal,
        settings: Settings,
        updated_by: str,
    ) -> None:
        atomic = usd_to_atomic(value)
        if atomic <= 0:
            raise ValueError("price must be positive")
        floor = cost_breakdown(settings, operation, str(value))["minimum_safe_price"]
        if value < floor:
            raise ValueError(f"price below floor {floor}")
        async with self._lock:
            await set_operation_price(session, operation, format(value, "f"), updated_by)
            self._cache.pop(operation, None)


pricing_registry = PricingRegistry()
