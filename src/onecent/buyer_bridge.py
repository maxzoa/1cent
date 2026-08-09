from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, cast
from urllib.parse import urlsplit

import httpx
from eth_account import Account
from eth_account.signers.local import LocalAccount
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
from x402 import x402Client
from x402.client_base import PaymentPolicy, RequirementsView
from x402.http import decode_payment_required_header, decode_payment_response_header
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client
from x402.schemas import AbortResult, PaymentCreationContext, PaymentRequired

from onecent.buyer_state import BuyerLedger, BuyerStateError, LedgerEntry
from onecent.buyer_wallet import load_private_key, wallet_status
from onecent.services.payment_outcome import PaymentEvidence, PaymentOutcome, classify_payment
from onecent.services.tool_catalog import TOOL_BY_KEY, TOOLS, ToolDefinition

BASE_URL = "https://1cent.maxzoa.ru"
BASE_MAINNET = "eip155:8453"
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
SELLER = "0x4798e8401ba3b1566685257c82d06303AB90EA35"
BRIDGE_VERSION = "0.7.1"


class BuyerBridgeError(RuntimeError):
    pass


class PaymentOutcomeUnknown(BuyerBridgeError):
    pass


class ApprovalRequired(BuyerBridgeError):
    def __init__(self, entry: LedgerEntry, state_path: Path) -> None:
        self.entry = entry
        self.state_path = state_path
        super().__init__("one-call payment approval required")

    def payload(self) -> dict[str, object]:
        return {
            "error": "PAYMENT_APPROVAL_REQUIRED",
            "tool": self.entry.tool,
            "amount_atomic": self.entry.amount_atomic,
            "amount_usdc": f"{self.entry.amount_atomic / 1_000_000:.6f}",
            "network": self.entry.network,
            "asset": self.entry.asset,
            "pay_to": _short_address(self.entry.pay_to),
            "expires_at": self.entry.expires_at,
            "approval_id": self.entry.entry_id,
            "next_action": (
                "Run: onecent approve "
                f"{self.entry.entry_id} --confirm-charge PAY-ONCE "
                f'--state-path "{self.state_path}"'
            ),
            "payment_executed": False,
        }


@dataclass(frozen=True)
class BridgePolicy:
    max_per_call_atomic: int
    daily_limit_atomic: int
    approval_mode: Literal["manual", "auto"] = "manual"
    base_url: str = BASE_URL
    timeout_seconds: float = 30.0


@dataclass(frozen=True)
class PaymentQuote:
    amount_atomic: int
    network: str
    asset: str
    pay_to: str
    resource: str


@dataclass(frozen=True)
class PaymentExecution:
    success: bool
    status_code: int
    result: object
    request_id: str | None
    payment_response_present: bool


def _short_address(value: str) -> str:
    return f"{value[:8]}…{value[-6:]}" if len(value) >= 16 else value


def validate_bridge_policy(policy: BridgePolicy) -> None:
    if policy.max_per_call_atomic <= 0:
        raise BuyerBridgeError("max per call must be positive")
    if policy.daily_limit_atomic < policy.max_per_call_atomic:
        raise BuyerBridgeError("daily spend cap must be at least the per-call cap")
    parsed = urlsplit(policy.base_url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise BuyerBridgeError("bridge base URL must be a credential-free HTTPS origin")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise BuyerBridgeError("bridge base URL must not include a path, query or fragment")


def validate_auto_mode(
    *,
    enabled: bool,
    confirm_network: str | None,
    confirm_asset: str | None,
    confirm_seller: str | None,
    confirm_charge: str | None,
) -> Literal["manual", "auto"]:
    if not enabled:
        return "manual"
    blockers: list[str] = []
    if confirm_network != BASE_MAINNET:
        blockers.append(f"--confirm-network must equal {BASE_MAINNET}")
    if (confirm_asset or "").lower() != BASE_USDC.lower():
        blockers.append("--confirm-asset must equal Base Mainnet USDC")
    if (confirm_seller or "").lower() != SELLER.lower():
        blockers.append("--confirm-seller must equal the 1cent seller")
    if confirm_charge != "ALLOW-CAPPED-PAYMENTS":
        blockers.append("--confirm-charge must equal ALLOW-CAPPED-PAYMENTS")
    if blockers:
        raise BuyerBridgeError("auto-pay blocked: " + "; ".join(blockers))
    return "auto"


def _requirement_matches(requirement: RequirementsView, quote: PaymentQuote) -> bool:
    pay_to = str(getattr(requirement, "pay_to", getattr(requirement, "payTo", "")))
    asset = str(getattr(requirement, "asset", ""))
    try:
        amount = int(requirement.get_amount())
    except (TypeError, ValueError):
        return False
    return (
        requirement.scheme == "exact"
        and requirement.network == quote.network
        and asset.lower() == quote.asset.lower()
        and pay_to.lower() == quote.pay_to.lower()
        and amount == quote.amount_atomic
    )


def exact_quote_policy(quote: PaymentQuote) -> PaymentPolicy:
    def policy(version: int, requirements: list[RequirementsView]) -> list[RequirementsView]:
        if version != 2:
            return []
        return [item for item in requirements if _requirement_matches(item, quote)]

    return policy


def _resource_guard(quote: PaymentQuote) -> Callable[[PaymentCreationContext], AbortResult | None]:
    def guard(context: PaymentCreationContext) -> AbortResult | None:
        required = context.payment_required
        if not isinstance(required, PaymentRequired):
            return AbortResult(reason="only x402 v2 is accepted")
        resource = required.resource.url if required.resource is not None else ""
        if resource != quote.resource:
            return AbortResult(reason="resource changed after approval")
        if not _requirement_matches(context.selected_requirements, quote):
            return AbortResult(reason="payment requirement changed after approval")
        return None

    return guard


def _payment_header(response: httpx.Response) -> str:
    header = response.headers.get("PAYMENT-REQUIRED") or response.headers.get("X-PAYMENT-REQUIRED")
    if not header:
        raise BuyerBridgeError("402 response has no PAYMENT-REQUIRED header")
    return str(header)


def _response_settlement_success(response: httpx.Response) -> bool:
    header = response.headers.get("PAYMENT-RESPONSE")
    if not header:
        return False
    try:
        settlement = decode_payment_response_header(header)
    except Exception:
        return False
    evidence = PaymentEvidence(
        http_status=response.status_code,
        header_success=settlement.success,
        network=settlement.network,
        transaction=settlement.transaction,
    )
    return classify_payment(evidence, BASE_MAINNET) is PaymentOutcome.SUCCESS


def parse_quote(
    required: PaymentRequired,
    *,
    expected_resource: str,
    max_per_call_atomic: int,
) -> PaymentQuote:
    if required.x402_version != 2:
        raise BuyerBridgeError("only x402 v2 is accepted")
    resource = required.resource.url if required.resource is not None else ""
    if resource != expected_resource:
        raise BuyerBridgeError("advertised resource does not match requested endpoint")
    matching = []
    for item in required.accepts:
        try:
            amount = int(item.amount)
        except (TypeError, ValueError):
            continue
        if (
            item.scheme == "exact"
            and item.network == BASE_MAINNET
            and item.asset.lower() == BASE_USDC.lower()
            and item.pay_to.lower() == SELLER.lower()
            and 0 < amount <= max_per_call_atomic
        ):
            matching.append((item, amount))
    if len(matching) != 1:
        raise BuyerBridgeError("challenge has no single safe payment option under local cap")
    selected, amount = matching[0]
    return PaymentQuote(
        amount_atomic=amount,
        network=selected.network,
        asset=selected.asset,
        pay_to=selected.pay_to,
        resource=resource,
    )


def request_fingerprint(tool: str, payload: dict[str, object], quote: PaymentQuote) -> str:
    canonical = json.dumps(
        {
            "tool": tool,
            "payload": payload,
            "amount_atomic": quote.amount_atomic,
            "network": quote.network,
            "asset": quote.asset.lower(),
            "pay_to": quote.pay_to.lower(),
            "resource": quote.resource,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class BuyerBridgeService:
    def __init__(self, policy: BridgePolicy, ledger: BuyerLedger) -> None:
        validate_bridge_policy(policy)
        self.policy = policy
        self.ledger = ledger

    async def _fetch_quote(self, tool_key: str, payload: dict[str, object]) -> PaymentQuote:
        definition = TOOL_BY_KEY[tool_key]
        resource = f"{self.policy.base_url.rstrip('/')}{definition.path}"
        async with httpx.AsyncClient(
            timeout=self.policy.timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": f"onecent-buyer-bridge/{BRIDGE_VERSION}"},
        ) as client:
            response = await client.post(resource, json=payload)
        if response.status_code != 402:
            raise BuyerBridgeError(
                f"expected unpaid HTTP 402 before signing, received {response.status_code}"
            )
        required = decode_payment_required_header(_payment_header(response))
        if not isinstance(required, PaymentRequired):
            raise BuyerBridgeError("only x402 v2 is accepted")
        return parse_quote(
            required,
            expected_resource=resource,
            max_per_call_atomic=self.policy.max_per_call_atomic,
        )

    @staticmethod
    def _load_account() -> LocalAccount:
        private_key, _source = load_private_key(required=True)
        if private_key is None:
            raise BuyerBridgeError("buyer wallet is not configured")
        try:
            return cast(LocalAccount, Account.from_key(private_key))
        except Exception as exc:
            raise BuyerBridgeError("local buyer private key is invalid") from exc

    async def _execute_payment(
        self,
        *,
        definition: ToolDefinition,
        payload: dict[str, object],
        quote: PaymentQuote,
        account: LocalAccount,
    ) -> PaymentExecution:
        client = x402Client().register_policy(exact_quote_policy(quote))
        client.on_before_payment_creation(_resource_guard(quote))
        register_exact_evm_client(client, EthAccountSigner(account))
        async with x402HttpxClient(
            client,
            timeout=self.policy.timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": f"onecent-buyer-bridge/{BRIDGE_VERSION}"},
        ) as paid_http:
            response = await paid_http.post(
                f"{self.policy.base_url.rstrip('/')}{definition.path}",
                json=payload,
            )
            await response.aread()
        payment_response_present = bool(response.headers.get("PAYMENT-RESPONSE"))
        settlement_success = _response_settlement_success(response)
        try:
            result: object = response.json()
        except ValueError:
            result = response.text[:1000]
        return PaymentExecution(
            success=settlement_success,
            status_code=response.status_code,
            result=result,
            request_id=response.headers.get("X-Request-ID"),
            payment_response_present=payment_response_present,
        )

    async def paid_call(
        self,
        tool_key: str,
        payload: dict[str, object],
    ) -> dict[str, object]:
        definition = TOOL_BY_KEY.get(tool_key)
        if definition is None:
            raise BuyerBridgeError("unknown 1cent tool")
        quote = await self._fetch_quote(tool_key, payload)
        fingerprint = request_fingerprint(tool_key, payload, quote)

        if self.policy.approval_mode == "manual":
            quoted = self.ledger.ensure_quote(
                fingerprint=fingerprint,
                tool=tool_key,
                amount_atomic=quote.amount_atomic,
                network=quote.network,
                asset=quote.asset,
                pay_to=quote.pay_to,
                resource=quote.resource,
            )
            if quoted.status != "approved":
                raise ApprovalRequired(quoted, self.ledger.path)

        account = self._load_account()
        if self.policy.approval_mode == "manual":
            reservation = self.ledger.reserve_approved(
                fingerprint=fingerprint,
                daily_limit_atomic=self.policy.daily_limit_atomic,
            )
        else:
            reservation = self.ledger.reserve_auto(
                fingerprint=fingerprint,
                tool=tool_key,
                amount_atomic=quote.amount_atomic,
                network=quote.network,
                asset=quote.asset,
                pay_to=quote.pay_to,
                resource=quote.resource,
                daily_limit_atomic=self.policy.daily_limit_atomic,
            )

        try:
            execution = await self._execute_payment(
                definition=definition,
                payload=payload,
                quote=quote,
                account=account,
            )
        except Exception as exc:
            self.ledger.finish(reservation.entry_id, status="unknown")
            raise PaymentOutcomeUnknown(
                "payment outcome UNKNOWN; automatic retry blocked for this request"
            ) from exc

        if not execution.success:
            self.ledger.finish(
                reservation.entry_id,
                status="unknown",
                request_id=execution.request_id,
                payment_response_present=execution.payment_response_present,
            )
            raise PaymentOutcomeUnknown(
                "payment outcome UNKNOWN; no successful PAYMENT-RESPONSE; automatic retry blocked"
            )

        self.ledger.finish(
            reservation.entry_id,
            status="success",
            request_id=execution.request_id,
            payment_response_present=True,
        )
        return {
            "payment": {
                "status": "settled",
                "amount_atomic": quote.amount_atomic,
                "amount_usdc": f"{quote.amount_atomic / 1_000_000:.6f}",
                "network": quote.network,
                "request_id": execution.request_id,
            },
            "result": execution.result,
        }

    async def get_public_json(self, path: str) -> object:
        async with httpx.AsyncClient(
            timeout=self.policy.timeout_seconds,
            follow_redirects=False,
            headers={"User-Agent": f"onecent-buyer-bridge/{BRIDGE_VERSION}"},
        ) as client:
            response = await client.get(f"{self.policy.base_url.rstrip('/')}{path}")
        response.raise_for_status()
        return response.json()

    async def catalog_search(self, query: str) -> dict[str, object]:
        catalog = await self.get_public_json("/v1/catalog")
        if not isinstance(catalog, list):
            raise BuyerBridgeError("live catalog response is invalid")
        words = {word for word in query.lower().replace("_", " ").split() if word}
        ranked: list[tuple[int, dict[str, object]]] = []
        for raw in catalog:
            if not isinstance(raw, dict):
                continue
            row = {str(key): value for key, value in raw.items()}
            haystack = " ".join(
                str(row.get(key, "")) for key in ("tool", "category", "description")
            ).lower()
            score = sum(word in haystack for word in words)
            if score or not words:
                ranked.append((score, row))
        ranked.sort(key=lambda item: (-item[0], str(item[1].get("tool", ""))))
        return {"results": [row for _, row in ranked[:5]]}

    def status(self) -> dict[str, object]:
        snapshot = self.ledger.snapshot()
        configured = wallet_status()
        return {
            "bridge_version": BRIDGE_VERSION,
            "mode": self.policy.approval_mode,
            "network": BASE_MAINNET,
            "asset": BASE_USDC,
            "seller": _short_address(SELLER),
            "max_per_call_atomic": self.policy.max_per_call_atomic,
            "daily_limit_atomic": self.policy.daily_limit_atomic,
            "daily_reserved_atomic": snapshot["daily_reserved_atomic"],
            "unresolved": snapshot["unresolved"],
            "approved": snapshot["approved"],
            "signer_configured": configured.configured,
            "signer_source": configured.source,
            "buyer": _short_address(configured.address or "") if configured.address else None,
            "wallet_secret_stored": False,
        }


def _annotations(*, open_world: bool) -> ToolAnnotations:
    return ToolAnnotations(
        readOnlyHint=True,
        destructiveHint=False,
        idempotentHint=False,
        openWorldHint=open_world,
    )


def _tool_error(exc: Exception) -> dict[str, object]:
    if isinstance(exc, ApprovalRequired):
        return exc.payload()
    if isinstance(exc, PaymentOutcomeUnknown):
        return {
            "error": "PAYMENT_OUTCOME_UNKNOWN",
            "message": str(exc),
            "payment_outcome": "UNKNOWN",
            "automatic_retry": False,
        }
    return {
        "error": type(exc).__name__,
        "message": str(exc),
        "payment_executed": False,
    }


def create_buyer_bridge(service: BuyerBridgeService) -> FastMCP[None]:
    bridge = FastMCP(
        name="1cent Buyer Bridge",
        instructions=(
            "Local safety bridge for 1cent. Wallet signing stays in this process. "
            "Manual mode requires a one-call terminal approval before every paid tool."
        ),
        website_url=BASE_URL,
    )

    @bridge.tool(
        name="buyer_bridge_status",
        title="1cent buyer bridge status",
        description=(
            "Show local signer readiness, approval mode, spend caps and unresolved outcomes. "
            "Never returns a private key or payment signature."
        ),
        annotations=_annotations(open_world=False),
    )
    async def buyer_bridge_status() -> dict[str, object]:
        return service.status()

    @bridge.tool(
        name="catalog_search",
        title="Find a 1cent tool and live price",
        description="Search the live 1cent catalog without payment or external URL fetch.",
        annotations=_annotations(open_world=False),
    )
    async def catalog_search(query: str) -> dict[str, object]:
        try:
            return await service.catalog_search(query)
        except Exception as exc:
            return _tool_error(exc)

    @bridge.tool(
        name="demo_url_pulse",
        title="Free static 1cent demo",
        description="Return the fixed precomputed URL Pulse sample without payment or URL fetch.",
        annotations=_annotations(open_world=False),
    )
    async def demo_url_pulse() -> object:
        try:
            return await service.get_public_json("/v1/demo/pulse")
        except Exception as exc:
            return _tool_error(exc)

    @bridge.tool(
        name="demo_live_url_pulse",
        title="Free live 1cent demo",
        description="Run the rate-limited safe service only against fixed example.com.",
        annotations=_annotations(open_world=True),
    )
    async def demo_live_url_pulse() -> object:
        try:
            return await service.get_public_json("/v1/demo/live-pulse")
        except Exception as exc:
            return _tool_error(exc)

    def register_standard(definition: ToolDefinition) -> None:
        async def paid_tool(url: str, fresh: bool = False) -> dict[str, object]:
            try:
                return await service.paid_call(
                    definition.key,
                    {"url": url, "fresh": fresh},
                )
            except (BuyerBridgeError, BuyerStateError) as exc:
                return _tool_error(exc)

        paid_tool.__name__ = definition.key
        bridge.tool(
            name=definition.key,
            title=definition.key.replace("_", " ").title(),
            description=(
                definition.description_en
                + " The local bridge validates the live x402 quote before signing."
            ),
            annotations=_annotations(open_world=True),
        )(paid_tool)

    for definition in TOOLS:
        if definition.key == "url_extract":

            async def url_extract(
                url: str,
                fresh: bool = False,
                include_links: bool = False,
            ) -> dict[str, object]:
                try:
                    return await service.paid_call(
                        "url_extract",
                        {"url": url, "fresh": fresh, "include_links": include_links},
                    )
                except (BuyerBridgeError, BuyerStateError) as exc:
                    return _tool_error(exc)

            bridge.tool(
                name="url_extract",
                title="URL Extract",
                description=(
                    definition.description_en
                    + " The local bridge validates the live x402 quote before signing."
                ),
                annotations=_annotations(open_world=True),
            )(url_extract)
        else:
            register_standard(definition)

    for tool_name in (
        "buyer_bridge_status",
        "catalog_search",
        "demo_url_pulse",
        "demo_live_url_pulse",
        *(item.key for item in TOOLS),
    ):
        tool = bridge._tool_manager.get_tool(tool_name)
        if tool is not None:
            tool.parameters["additionalProperties"] = False
            tool.fn_metadata.arg_model.model_config["extra"] = "forbid"
            tool.fn_metadata.arg_model.model_rebuild(force=True)
    return bridge
