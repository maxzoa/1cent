from onecent.repositories.payments import daily_limit_allows


def test_daily_limits_allow_safe_reservation() -> None:
    assert daily_limit_allows(0, 0, 10_000, 10, 1_000_000)


def test_daily_settlement_limit_blocks() -> None:
    assert not daily_limit_allows(10, 100_000, 10_000, 10, 1_000_000)


def test_daily_revenue_limit_blocks_overage() -> None:
    assert not daily_limit_allows(2, 995_000, 10_000, 10, 1_000_000)


def test_daily_revenue_limit_allows_exact_floor() -> None:
    assert daily_limit_allows(2, 990_000, 10_000, 10, 1_000_000)


def test_unlimited_settlement_mode_ignores_usage() -> None:
    for count in (10, 100, 1_000):
        assert daily_limit_allows(
            count,
            0,
            10_000,
            10,
            1_000_000,
            settlement_limit_enabled=False,
        )


def test_unlimited_revenue_mode_ignores_usage() -> None:
    for revenue in (1_000_000, 10_000_000, 1_000_000_000):
        assert daily_limit_allows(
            0,
            revenue,
            10_000,
            10,
            1_000_000,
            revenue_limit_enabled=False,
        )


def test_fully_unlimited_ignores_existing_used_and_pending() -> None:
    assert daily_limit_allows(
        1_000,
        1_000_000_000,
        10_000,
        10,
        1_000_000,
        settlement_limit_enabled=False,
        revenue_limit_enabled=False,
    )
