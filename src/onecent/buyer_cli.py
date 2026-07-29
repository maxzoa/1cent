import argparse
import asyncio
import getpass
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from typing import Any

import httpx
from eth_account import Account
from x402 import x402Client
from x402.client import max_amount
from x402.http import decode_payment_required_header
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

from onecent.buyer_bridge import (
    BASE_USDC,
    SELLER,
    BridgePolicy,
    BuyerBridgeError,
    BuyerBridgeService,
    create_buyer_bridge,
    validate_auto_mode,
)
from onecent.buyer_state import BuyerLedger, BuyerStateError, default_state_path
from onecent.buyer_wallet import (
    BuyerWalletError,
    delete_private_key,
    store_private_key,
    wallet_status,
)

DEFAULT_BASE_URL = "https://1cent.maxzoa.ru"
DEFAULT_ENDPOINT = "/v1/url/status"
BASE_MAINNET = "eip155:8453"
USDC_DECIMALS = 6


class BuyerSafetyError(RuntimeError):
    pass


def atomic_from_usdc(value: str) -> int:
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise BuyerSafetyError("invalid USDC amount") from exc
    atomic = amount * (10**USDC_DECIMALS)
    if amount <= 0 or atomic != atomic.to_integral_value():
        raise BuyerSafetyError("USDC amount must be positive with at most 6 decimals")
    return int(atomic)


def validate_requirement(requirement: dict[str, Any]) -> list[str]:
    blockers: list[str] = []
    if requirement.get("scheme") != "exact":
        blockers.append("scheme is not exact")
    if requirement.get("network") != BASE_MAINNET:
        blockers.append("network is not Base Mainnet eip155:8453")
    if str(requirement.get("asset", "")).lower() != BASE_USDC.lower():
        blockers.append("asset is not Base Mainnet USDC")
    if str(requirement.get("payTo", "")).lower() != SELLER.lower():
        blockers.append("seller address mismatch")
    try:
        if int(str(requirement.get("amount"))) <= 0:
            blockers.append("amount is not positive")
    except (TypeError, ValueError):
        blockers.append("amount is invalid")
    return blockers


def _short_address(value: str) -> str:
    return f"{value[:8]}…{value[-6:]}" if len(value) >= 16 else value


async def _balance_atomic(rpc_url: str, buyer_address: str) -> int:
    address = buyer_address.removeprefix("0x")
    if len(address) != 40 or any(char not in "0123456789abcdefABCDEF" for char in address):
        raise BuyerSafetyError("buyer address is not a valid EVM address")
    data = "0x70a08231" + address.lower().rjust(64, "0")
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_call",
        "params": [{"to": BASE_USDC, "data": data}, "latest"],
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(rpc_url, json=body)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, dict) or not isinstance(payload.get("result"), str):
        raise BuyerSafetyError("RPC did not return a USDC balance")
    return int(payload["result"], 16)


def _challenge_header(response: httpx.Response) -> str:
    value = response.headers.get("PAYMENT-REQUIRED") or response.headers.get("X-PAYMENT-REQUIRED")
    if not value:
        raise BuyerSafetyError("402 response has no PAYMENT-REQUIRED header")
    return str(value)


async def doctor(args: argparse.Namespace) -> int:
    base_url = args.base_url.rstrip("/")
    async with httpx.AsyncClient(timeout=args.timeout, follow_redirects=False) as client:
        health = await client.get(f"{base_url}/health")
        info = await client.get(f"{base_url}/info")
        challenge = await client.post(
            f"{base_url}{args.endpoint}",
            json={"url": "https://example.com/", "fresh": False},
            headers={"User-Agent": "onecent-buyer-doctor/0.4"},
        )
    blockers: list[str] = []
    if health.status_code != 200:
        blockers.append(f"health HTTP {health.status_code}")
    if info.status_code != 200:
        blockers.append(f"info HTTP {info.status_code}")
    if challenge.status_code != 402:
        blockers.append(f"expected HTTP 402, received {challenge.status_code}")
        requirement: dict[str, Any] = {}
    else:
        decoded = decode_payment_required_header(_challenge_header(challenge))
        accepts = decoded.model_dump(by_alias=True, mode="json").get("accepts", [])
        requirement = accepts[0] if accepts else {}
        if not requirement:
            blockers.append("challenge has no accepted payment requirement")
        else:
            blockers.extend(validate_requirement(requirement))
    balance: int | None = None
    if args.rpc_url or args.buyer_address:
        if not args.rpc_url or not args.buyer_address:
            blockers.append("balance check requires both --rpc-url and --buyer-address")
        else:
            balance = await _balance_atomic(args.rpc_url, args.buyer_address)
            if requirement and balance < int(requirement["amount"]):
                blockers.append("buyer USDC balance is below the advertised price")
    output = {
        "ready": not blockers,
        "payment_executed": False,
        "health": health.status_code,
        "info": info.status_code,
        "challenge": challenge.status_code,
        "network": requirement.get("network"),
        "asset": requirement.get("asset"),
        "amount_atomic": requirement.get("amount"),
        "pay_to": _short_address(str(requirement.get("payTo", ""))),
        "buyer_balance_atomic": balance,
        "blockers": blockers,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if not blockers else 1


def validate_paid_confirmation(args: argparse.Namespace) -> int:
    if not args.pay:
        raise BuyerSafetyError("payment disabled: add --pay only after reviewing the 402 challenge")
    if args.confirm_network != BASE_MAINNET:
        raise BuyerSafetyError(f"refusing payment: --confirm-network must equal {BASE_MAINNET}")
    if args.confirm_charge != "PAY-ONCE":
        raise BuyerSafetyError("refusing payment: --confirm-charge must equal PAY-ONCE")
    return atomic_from_usdc(args.max_usdc)


def approve_bridge_call(args: argparse.Namespace) -> int:
    if args.confirm_charge != "PAY-ONCE":
        raise BuyerBridgeError("--confirm-charge must equal PAY-ONCE")
    ledger = BuyerLedger(args.state_path)
    entry = ledger.approve(args.approval_id)
    print(
        json.dumps(
            {
                "approved": True,
                "approval_id": entry.entry_id,
                "tool": entry.tool,
                "amount_atomic": entry.amount_atomic,
                "network": entry.network,
                "pay_to": _short_address(entry.pay_to),
                "expires_at": entry.expires_at,
                "payment_executed": False,
                "next_action": "Repeat the same MCP tool call once.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def bridge_state(args: argparse.Namespace) -> int:
    ledger = BuyerLedger(args.state_path)
    print(json.dumps(ledger.snapshot(), ensure_ascii=False, indent=2))
    return 0


def wallet_command(args: argparse.Namespace) -> int:
    if args.wallet_action == "set":
        private_key = getpass.getpass("Buyer private key (hidden): ")
        address = store_private_key(private_key)
        print(
            json.dumps(
                {
                    "configured": True,
                    "storage": "OS keyring",
                    "buyer": _short_address(address),
                    "secret_printed": False,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.wallet_action == "delete":
        if args.confirm_delete != "DELETE-WALLET":
            raise BuyerWalletError("--confirm-delete must equal DELETE-WALLET")
        delete_private_key()
        print("buyer_wallet_deleted=true")
        return 0
    status = wallet_status()
    print(
        json.dumps(
            {
                "configured": status.configured,
                "source": status.source,
                "buyer": _short_address(status.address or "") if status.address else None,
                "secret_printed": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def run_bridge(args: argparse.Namespace) -> None:
    approval_mode = validate_auto_mode(
        enabled=args.auto_pay,
        confirm_network=args.confirm_network,
        confirm_asset=args.confirm_asset,
        confirm_seller=args.confirm_seller,
        confirm_charge=args.confirm_charge,
    )
    policy = BridgePolicy(
        max_per_call_atomic=atomic_from_usdc(args.max_usdc_per_call),
        daily_limit_atomic=atomic_from_usdc(args.daily_limit_usdc),
        approval_mode=approval_mode,
        base_url=args.base_url,
        timeout_seconds=args.timeout,
    )
    service = BuyerBridgeService(policy, BuyerLedger(args.state_path))
    bridge = create_buyer_bridge(service)
    bridge.run(transport="stdio")


async def paid_call(args: argparse.Namespace) -> int:
    max_atomic = validate_paid_confirmation(args)
    private_key = os.getenv("ONECENT_BUYER_PRIVATE_KEY")
    if not private_key:
        raise BuyerSafetyError("ONECENT_BUYER_PRIVATE_KEY is not configured")
    account = Account.from_key(private_key)
    client = x402Client().register_policy(max_amount(max_atomic))
    register_exact_evm_client(client, EthAccountSigner(account))
    payload = {"url": args.url, "fresh": args.fresh}
    try:
        async with x402HttpxClient(
            client,
            timeout=args.timeout,
            follow_redirects=False,
            headers={"User-Agent": "onecent-buyer-cli/0.4"},
        ) as http:
            response = await http.post(f"{args.base_url.rstrip('/')}{args.endpoint}", json=payload)
            await response.aread()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "UNKNOWN",
                    "automatic_retry": False,
                    "message": f"request outcome is unknown: {type(exc).__name__}",
                },
                ensure_ascii=False,
            )
        )
        return 2
    output: dict[str, Any] = {
        "status": "SUCCESS" if response.status_code == 200 else "FAILED",
        "http_status": response.status_code,
        "request_id": response.headers.get("X-Request-ID"),
        "payment_response_present": bool(response.headers.get("PAYMENT-RESPONSE")),
    }
    try:
        output["result"] = response.json()
    except ValueError:
        output["result"] = response.text[:1000]
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if response.status_code == 200 else 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="onecent", description="Safety-first 1cent buyer CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    doctor_parser = subparsers.add_parser("doctor", help="check service and 402; never pay")
    doctor_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    doctor_parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    doctor_parser.add_argument("--buyer-address")
    doctor_parser.add_argument("--rpc-url")
    doctor_parser.add_argument("--timeout", type=float, default=20.0)
    call_parser = subparsers.add_parser("call", help="perform one explicitly confirmed paid call")
    call_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    call_parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    call_parser.add_argument("--url", default="https://example.com/")
    call_parser.add_argument("--fresh", action="store_true")
    call_parser.add_argument("--timeout", type=float, default=30.0)
    call_parser.add_argument("--pay", action="store_true")
    call_parser.add_argument("--max-usdc", required=True)
    call_parser.add_argument("--confirm-network")
    call_parser.add_argument("--confirm-charge")
    bridge_parser = subparsers.add_parser(
        "bridge",
        help="run the local stdio MCP buyer bridge; manual approval is the default",
    )
    bridge_parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    bridge_parser.add_argument("--max-usdc-per-call", required=True)
    bridge_parser.add_argument("--daily-limit-usdc", required=True)
    bridge_parser.add_argument("--state-path", default=str(default_state_path()))
    bridge_parser.add_argument("--timeout", type=float, default=30.0)
    bridge_parser.add_argument("--auto-pay", action="store_true")
    bridge_parser.add_argument("--confirm-network")
    bridge_parser.add_argument("--confirm-asset")
    bridge_parser.add_argument("--confirm-seller")
    bridge_parser.add_argument("--confirm-charge")
    approve_parser = subparsers.add_parser(
        "approve",
        help="approve exactly one quoted bridge call; this command never pays",
    )
    approve_parser.add_argument("approval_id")
    approve_parser.add_argument("--confirm-charge", required=True)
    approve_parser.add_argument("--state-path", default=str(default_state_path()))
    state_parser = subparsers.add_parser(
        "bridge-state",
        help="show local bridge spend and unresolved outcome counts",
    )
    state_parser.add_argument("--state-path", default=str(default_state_path()))
    wallet_parser = subparsers.add_parser(
        "wallet",
        help="store, inspect or delete the local buyer signer using the OS keyring",
    )
    wallet_parser.add_argument("wallet_action", choices=("set", "status", "delete"))
    wallet_parser.add_argument("--confirm-delete")
    return parser


async def _async_main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "doctor":
        return await doctor(args)
    if args.command == "approve":
        return approve_bridge_call(args)
    if args.command == "bridge-state":
        return bridge_state(args)
    if args.command == "wallet":
        return wallet_command(args)
    if args.command == "bridge":
        raise BuyerBridgeError("bridge must be started by the synchronous CLI entrypoint")
    return await paid_call(args)


def main() -> None:
    try:
        args = _parser().parse_args()
        if args.command == "bridge":
            run_bridge(args)
            return
        raise SystemExit(asyncio.run(_async_main(sys.argv[1:])))
    except (BuyerSafetyError, BuyerBridgeError, BuyerStateError, BuyerWalletError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
