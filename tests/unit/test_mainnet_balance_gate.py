from scripts.check_mainnet_balances import has_minimum_usdc


def test_balance_gate_rejects_below_payment_amount() -> None:
    assert not has_minimum_usdc(9_999, 10_000)


def test_balance_gate_accepts_exact_payment_amount() -> None:
    assert has_minimum_usdc(10_000, 10_000)


def test_balance_gate_accepts_larger_balance() -> None:
    assert has_minimum_usdc(1_000_000, 10_000)
