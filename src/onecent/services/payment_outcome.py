from dataclasses import dataclass
from enum import Enum


class PaymentOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    UNKNOWN = "unknown"


NETWORK_ALIASES = {
    "base": "eip155:8453",
    "base-sepolia": "eip155:84532",
}


@dataclass(frozen=True)
class PaymentEvidence:
    http_status: int
    header_success: bool | None
    network: str | None
    transaction: str | None
    receipt_status: int | None = None


def canonical_network(network: str | None) -> str | None:
    if network is None:
        return None
    return NETWORK_ALIASES.get(network.lower(), network)


def classify_payment(evidence: PaymentEvidence, expected_network: str) -> PaymentOutcome:
    if evidence.http_status != 200:
        return PaymentOutcome.UNKNOWN
    if evidence.header_success is False:
        return PaymentOutcome.FAILURE
    if evidence.header_success is not True or not evidence.transaction:
        return PaymentOutcome.UNKNOWN
    if canonical_network(evidence.network) != expected_network:
        return PaymentOutcome.UNKNOWN
    if evidence.receipt_status == 0:
        return PaymentOutcome.FAILURE
    if evidence.receipt_status not in (None, 1):
        return PaymentOutcome.UNKNOWN
    return PaymentOutcome.SUCCESS


def allow_idempotent_retry(outcome: PaymentOutcome) -> bool:
    return outcome is PaymentOutcome.SUCCESS


def allow_new_payment_id_after_result(outcome: PaymentOutcome) -> bool:
    # A new payment ID after any submitted payment could create a second settlement.
    return False
