import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from onecent.services.payments import _EffectivePriceCache, _fallback_payment_id


def test_fallback_payment_id_is_stable_and_payload_bound() -> None:
    first = _fallback_payment_id("signed-payload-a")
    assert first == _fallback_payment_id("signed-payload-a")
    assert first != _fallback_payment_id("signed-payload-b")
    assert first.startswith("auto_")
    assert len(first) == 69
    assert first.replace("auto_", "", 1).isalnum()


@pytest.mark.asyncio
async def test_price_cache_collapses_concurrent_production_reads() -> None:
    loader = AsyncMock(return_value=1000)
    cache = _EffectivePriceCache(loader, ttl_seconds=10)
    settings = SimpleNamespace(app_env="production")

    values = await asyncio.gather(*(cache.get(settings, "url_status") for _ in range(20)))

    assert values == [1000] * 20
    loader.assert_awaited_once_with(settings, "url_status")


@pytest.mark.asyncio
async def test_price_cache_is_bypassed_in_tests() -> None:
    loader = AsyncMock(side_effect=[1000, 2000])
    cache = _EffectivePriceCache(loader, ttl_seconds=10)
    settings = SimpleNamespace(app_env="test")

    assert await cache.get(settings, "url_status") == 1000
    assert await cache.get(settings, "url_status") == 2000
    assert loader.await_count == 2


@pytest.mark.asyncio
async def test_price_cache_refreshes_after_ttl() -> None:
    loader = AsyncMock(side_effect=[1000, 2000])
    cache = _EffectivePriceCache(loader, ttl_seconds=0.001)
    settings = SimpleNamespace(app_env="production")

    assert await cache.get(settings, "url_status") == 1000
    await asyncio.sleep(0.01)
    assert await cache.get(settings, "url_status") == 2000
