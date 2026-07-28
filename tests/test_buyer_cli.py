from argparse import Namespace

import pytest

from onecent.buyer_cli import (
    BASE_MAINNET,
    BASE_USDC,
    SELLER,
    BuyerSafetyError,
    atomic_from_usdc,
    validate_paid_confirmation,
    validate_requirement,
)


def _requirement() -> dict[str, object]:
    return {
        "scheme": "exact",
        "network": BASE_MAINNET,
        "asset": BASE_USDC,
        "amount": "1000",
        "payTo": SELLER,
    }


def test_atomic_from_usdc_is_exact() -> None:
    assert atomic_from_usdc("0.001") == 1_000
    with pytest.raises(BuyerSafetyError):
        atomic_from_usdc("0.0000001")


def test_requirement_accepts_only_expected_mainnet_payment() -> None:
    assert validate_requirement(_requirement()) == []
    wrong = _requirement() | {"network": "eip155:84532"}
    assert "network is not Base Mainnet eip155:8453" in validate_requirement(wrong)


@pytest.mark.parametrize(
    ("pay", "network", "confirmation"),
    [
        (False, BASE_MAINNET, "PAY-ONCE"),
        (True, "eip155:84532", "PAY-ONCE"),
        (True, BASE_MAINNET, "no"),
    ],
)
def test_paid_call_requires_three_explicit_gates(
    pay: bool, network: str, confirmation: str
) -> None:
    args = Namespace(
        pay=pay,
        confirm_network=network,
        confirm_charge=confirmation,
        max_usdc="0.001",
    )
    with pytest.raises(BuyerSafetyError):
        validate_paid_confirmation(args)


def test_paid_call_returns_atomic_cap_after_all_gates() -> None:
    args = Namespace(
        pay=True,
        confirm_network=BASE_MAINNET,
        confirm_charge="PAY-ONCE",
        max_usdc="0.001",
    )
    assert validate_paid_confirmation(args) == 1_000
