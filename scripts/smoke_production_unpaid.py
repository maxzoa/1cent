import argparse
import asyncio

import httpx
from x402.http import decode_payment_required_header

NETWORK = "eip155:8453"
ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PAY_TO = "0x4798e8401ba3b1566685257c82d06303AB90EA35"


async def run(base_url: str) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        health = await client.get(f"{base_url}/health")
        info = await client.get(f"{base_url}/info")
        docs = await client.get(f"{base_url}/docs")
        openapi = await client.get(f"{base_url}/openapi.json")
        unpaid_responses = {
            operation: await client.post(
                f"{base_url}/v1/url/{operation}",
                json={"url": "https://example.com", "fresh": False},
            )
            for operation in ("pulse", "passport", "extract", "changed")
        }
    assert health.status_code == 200 and health.json()["status"] == "ok"
    assert info.json()["network"] == NETWORK
    assert info.json()["facilitator"] == "https://facilitator.payai.network"
    assert docs.status_code == 200 and openapi.status_code == 200
    expected = {"pulse": "3000", "passport": "10000", "extract": "10000", "changed": "3000"}
    for operation, unpaid in unpaid_responses.items():
        assert unpaid.status_code == 402
        required = decode_payment_required_header(unpaid.headers["payment-required"])
        accepted = required.accepts[0]
        assert str(accepted.network) == NETWORK
        assert accepted.asset.lower() == ASSET.lower()
        assert accepted.amount == expected[operation]
        assert accepted.pay_to.lower() == PAY_TO.lower()
        assert "bazaar" in (required.extensions or {})
    print("rest_amounts=" + ",".join(f"{key}:{value}" for key, value in expected.items()))
    print("production_unpaid=PASS; REST_402=PASS; metadata=PASS; no_payment=PASS")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    args = parser.parse_args()
    asyncio.run(run(args.base_url))


if __name__ == "__main__":
    main()
