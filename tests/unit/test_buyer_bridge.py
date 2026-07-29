from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock

import httpx
import pytest
from x402.http import encode_payment_response_header
from x402.schemas import PaymentRequired, SettleResponse

from onecent.buyer_bridge import (
    BASE_MAINNET,
    BASE_URL,
    BASE_USDC,
    SELLER,
    ApprovalRequired,
    BridgePolicy,
    BuyerBridgeError,
    BuyerBridgeService,
    PaymentExecution,
    PaymentOutcomeUnknown,
    PaymentQuote,
    _response_settlement_success,
    create_buyer_bridge,
    parse_quote,
    validate_auto_mode,
)
from onecent.buyer_state import BuyerLedger, BuyerStateError
from onecent.services.tool_catalog import TOOL_BY_KEY

TEST_PRIVATE_KEY = "0x" + "11" * 32


def _settlement_response(*, success: bool = True, network: str = "base") -> httpx.Response:
    header = encode_payment_response_header(
        SettleResponse(
            success=success,
            network=network,
            transaction="0xfixture" if success else "",
            errorReason=None if success else "rejected",
        )
    )
    return httpx.Response(200, headers={"PAYMENT-RESPONSE": header})


def _required(**overrides: object) -> PaymentRequired:
    requirement = {
        "scheme": "exact",
        "network": BASE_MAINNET,
        "asset": BASE_USDC,
        "amount": "1000",
        "payTo": SELLER,
        "maxTimeoutSeconds": 60,
    }
    requirement.update(overrides)
    return PaymentRequired.model_validate(
        {
            "x402Version": 2,
            "resource": {"url": f"{BASE_URL}/v1/url/status"},
            "accepts": [requirement],
        }
    )


def _quote() -> PaymentQuote:
    return PaymentQuote(
        amount_atomic=1000,
        network=BASE_MAINNET,
        asset=BASE_USDC,
        pay_to=SELLER,
        resource=f"{BASE_URL}/v1/url/status",
    )


def _service(tmp_path: Path, *, mode: str = "manual", daily: int = 10_000) -> BuyerBridgeService:
    policy = BridgePolicy(
        max_per_call_atomic=1000,
        daily_limit_atomic=daily,
        approval_mode="auto" if mode == "auto" else "manual",
    )
    return BuyerBridgeService(policy, BuyerLedger(tmp_path / "bridge.sqlite3"))


def test_quote_accepts_only_exact_pinned_payment() -> None:
    quote = parse_quote(
        _required(),
        expected_resource=f"{BASE_URL}/v1/url/status",
        max_per_call_atomic=1000,
    )
    assert quote == _quote()

    for override in (
        {"network": "eip155:84532"},
        {"asset": "0x" + "22" * 20},
        {"payTo": "0x" + "33" * 20},
        {"amount": "1001"},
        {"scheme": "upto"},
    ):
        with pytest.raises(BuyerBridgeError):
            parse_quote(
                _required(**override),
                expected_resource=f"{BASE_URL}/v1/url/status",
                max_per_call_atomic=1000,
            )


def test_actual_x402_success_header_is_required_for_success() -> None:
    assert _response_settlement_success(_settlement_response()) is True
    assert _response_settlement_success(_settlement_response(success=False)) is False
    assert _response_settlement_success(_settlement_response(network="eip155:84532")) is False
    assert _response_settlement_success(httpx.Response(200)) is False


def test_quote_rejects_resource_substitution() -> None:
    with pytest.raises(BuyerBridgeError, match="resource"):
        parse_quote(
            _required(),
            expected_resource=f"{BASE_URL}/v1/url/pulse",
            max_per_call_atomic=1000,
        )


def test_auto_mode_needs_all_explicit_owner_gates() -> None:
    assert (
        validate_auto_mode(
            enabled=False,
            confirm_network=None,
            confirm_asset=None,
            confirm_seller=None,
            confirm_charge=None,
        )
        == "manual"
    )
    with pytest.raises(BuyerBridgeError, match="auto-pay blocked"):
        validate_auto_mode(
            enabled=True,
            confirm_network=BASE_MAINNET,
            confirm_asset=BASE_USDC,
            confirm_seller=SELLER,
            confirm_charge="wrong",
        )
    assert (
        validate_auto_mode(
            enabled=True,
            confirm_network=BASE_MAINNET,
            confirm_asset=BASE_USDC,
            confirm_seller=SELLER,
            confirm_charge="ALLOW-CAPPED-PAYMENTS",
        )
        == "auto"
    )


@pytest.mark.asyncio
async def test_manual_mode_quotes_then_executes_once_after_approval(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path)
    fetch_quote = AsyncMock(return_value=_quote())
    execute = AsyncMock(
        return_value=PaymentExecution(
            success=True,
            status_code=200,
            result={"status": 200},
            request_id="req-1",
            payment_response_present=True,
        )
    )
    monkeypatch.setattr(service, "_fetch_quote", fetch_quote)
    monkeypatch.setattr(service, "_execute_payment", execute)
    monkeypatch.setenv("ONECENT_BUYER_PRIVATE_KEY", TEST_PRIVATE_KEY)
    payload: dict[str, object] = {"url": "https://example.com/", "fresh": False}

    with pytest.raises(ApprovalRequired) as approval:
        await service.paid_call("url_status", payload)
    assert execute.await_count == 0
    assert approval.value.payload()["payment_executed"] is False

    service.ledger.approve(approval.value.entry.entry_id)
    result = await service.paid_call("url_status", payload)
    assert execute.await_count == 1
    assert result["payment"] == {
        "status": "settled",
        "amount_atomic": 1000,
        "amount_usdc": "0.001000",
        "network": BASE_MAINNET,
        "request_id": "req-1",
    }
    assert service.ledger.snapshot()["daily_reserved_atomic"] == 1000


@pytest.mark.asyncio
async def test_unknown_never_retries_same_request(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path, mode="auto")
    execute = AsyncMock(side_effect=TimeoutError("simulated timeout"))
    monkeypatch.setattr(service, "_fetch_quote", AsyncMock(return_value=_quote()))
    monkeypatch.setattr(service, "_execute_payment", execute)
    monkeypatch.setenv("ONECENT_BUYER_PRIVATE_KEY", TEST_PRIVATE_KEY)
    payload: dict[str, object] = {"url": "https://example.com/", "fresh": False}

    with pytest.raises(PaymentOutcomeUnknown):
        await service.paid_call("url_status", payload)
    with pytest.raises(BuyerStateError, match="automatic retry is blocked"):
        await service.paid_call("url_status", payload)
    assert execute.await_count == 1
    assert service.ledger.snapshot()["unresolved"] == 1


@pytest.mark.asyncio
async def test_daily_cap_counts_success_and_blocks_next_payment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    service = _service(tmp_path, mode="auto", daily=1000)
    monkeypatch.setattr(service, "_fetch_quote", AsyncMock(return_value=_quote()))
    execute = AsyncMock(
        return_value=PaymentExecution(
            success=True,
            status_code=200,
            result={},
            request_id="req-2",
            payment_response_present=True,
        )
    )
    monkeypatch.setattr(service, "_execute_payment", execute)
    monkeypatch.setenv("ONECENT_BUYER_PRIVATE_KEY", TEST_PRIVATE_KEY)

    await service.paid_call(
        "url_status", {"url": "https://example.com/one", "fresh": False}
    )
    with pytest.raises(BuyerStateError, match="daily spend cap"):
        await service.paid_call(
            "url_status", {"url": "https://example.com/two", "fresh": False}
        )
    assert execute.await_count == 1


def test_local_state_contains_no_private_key(tmp_path: Path) -> None:
    state_path = tmp_path / "bridge.sqlite3"
    ledger = BuyerLedger(state_path)
    ledger.ensure_quote(
        fingerprint="a" * 64,
        tool="url_status",
        amount_atomic=1000,
        network=BASE_MAINNET,
        asset=BASE_USDC,
        pay_to=SELLER,
        resource=f"{BASE_URL}/v1/url/status",
    )
    assert TEST_PRIVATE_KEY.encode() not in state_path.read_bytes()


@pytest.mark.asyncio
async def test_bridge_exports_all_tools_with_strict_input_schemas(tmp_path: Path) -> None:
    bridge = create_buyer_bridge(_service(tmp_path))
    tools = await bridge.list_tools()
    expected = set(TOOL_BY_KEY) | {
        "buyer_bridge_status",
        "catalog_search",
        "demo_url_pulse",
        "demo_live_url_pulse",
    }
    assert {tool.name for tool in tools} == expected
    for tool in tools:
        assert tool.inputSchema["additionalProperties"] is False


def test_approval_error_does_not_claim_payment_happened(tmp_path: Path) -> None:
    ledger = BuyerLedger(tmp_path / "bridge.sqlite3")
    entry = ledger.ensure_quote(
        fingerprint="b" * 64,
        tool="url_status",
        amount_atomic=1000,
        network=BASE_MAINNET,
        asset=BASE_USDC,
        pay_to=SELLER,
        resource=f"{BASE_URL}/v1/url/status",
    )
    payload = ApprovalRequired(entry, ledger.path).payload()
    assert payload["payment_executed"] is False
    assert "PAY-ONCE" in str(payload["next_action"])
