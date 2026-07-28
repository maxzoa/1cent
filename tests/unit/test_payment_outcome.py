import json
from pathlib import Path

from onecent.services.payment_outcome import (
    PaymentEvidence,
    PaymentOutcome,
    allow_idempotent_retry,
    allow_new_payment_id_after_result,
    classify_payment,
)

FIXTURE = Path(__file__).parents[1] / "fixtures" / "payai_mainnet_success_anonymized.json"
MAINNET = "eip155:8453"


def test_actual_payai_success_fixture_is_success() -> None:
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    evidence = PaymentEvidence(
        http_status=payload["evidence"]["httpStatus"],
        header_success=payload["success"],
        network=payload["network"],
        transaction=payload["transaction"],
        receipt_status=payload["evidence"]["receiptStatus"],
    )
    assert classify_payment(evidence, MAINNET) is PaymentOutcome.SUCCESS


def test_http_200_receipt_and_transaction_are_success() -> None:
    evidence = PaymentEvidence(200, True, "eip155:8453", "0xfixture", 1)
    assert classify_payment(evidence, MAINNET) is PaymentOutcome.SUCCESS


def test_explicit_false_is_failure() -> None:
    evidence = PaymentEvidence(200, False, "base", "0xfixture", 1)
    assert classify_payment(evidence, MAINNET) is PaymentOutcome.FAILURE


def test_ambiguous_result_does_not_retry() -> None:
    evidence = PaymentEvidence(200, None, "base", None, None)
    outcome = classify_payment(evidence, MAINNET)
    assert outcome is PaymentOutcome.UNKNOWN
    assert not allow_idempotent_retry(outcome)


def test_unknown_result_never_creates_new_payment_id() -> None:
    assert not allow_new_payment_id_after_result(PaymentOutcome.UNKNOWN)
