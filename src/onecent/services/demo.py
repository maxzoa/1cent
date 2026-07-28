from typing import Any


def demo_pulse_result() -> dict[str, Any]:
    """Return a static product sample without payment, network, DB or URL fetch."""
    return {
        "demo": True,
        "url": "https://example.com",
        "reachable": True,
        "status_code": 200,
        "title": "Example Domain",
        "summary": (
            "Precomputed 1cent response sample. Paid tools inspect the buyer-selected "
            "public URL after successful x402 settlement."
        ),
        "source": "precomputed",
        "network_request_performed": False,
        "payment_required": False,
    }
