from onecent.services.payments import _fallback_payment_id


def test_fallback_payment_id_is_stable_and_payload_bound() -> None:
    first = _fallback_payment_id("signed-payload-a")
    assert first == _fallback_payment_id("signed-payload-a")
    assert first != _fallback_payment_id("signed-payload-b")
    assert first.startswith("auto_")
    assert len(first) == 69
    assert first.replace("auto_", "", 1).isalnum()
