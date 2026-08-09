from __future__ import annotations

import argparse
from typing import Any, cast

import httpx
from x402.http import decode_payment_required_header

NETWORK = "eip155:8453"
ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PAY_TO = "0x4798e8401ba3b1566685257c82d06303AB90EA35"


def run(base_url: str) -> None:
    with httpx.Client(
        base_url=base_url,
        timeout=30,
        headers={"User-Agent": "onecent-smoke/1.0"},
    ) as client:
        response = client.get("/v1/catalog")
        response.raise_for_status()
        catalog = cast(list[dict[str, Any]], response.json())
        if len(catalog) != 43:
            raise RuntimeError(f"expected 43 paid tools, got {len(catalog)}")
        for item in catalog:
            tool = str(item["tool"])
            payload = (
                {"urls": ["https://example.com", "https://www.iana.org"], "fresh": False}
                if tool == "batch_url_status"
                else {"url": "https://example.com", "fresh": False}
            )
            unpaid = client.post(str(item["rest_path"]), json=payload)
            if unpaid.status_code != 402:
                raise RuntimeError(f"{tool}: expected 402, got {unpaid.status_code}")
            required = decode_payment_required_header(unpaid.headers["payment-required"])
            accepted = required.accepts[0]
            multiplier = 2 if tool == "batch_url_status" else 1
            expected = int(item["price_atomic"]) * multiplier
            if str(accepted.network) != NETWORK:
                raise RuntimeError(f"{tool}: wrong network")
            if str(accepted.asset).lower() != ASSET.lower():
                raise RuntimeError(f"{tool}: wrong asset")
            if str(accepted.pay_to).lower() != PAY_TO.lower():
                raise RuntimeError(f"{tool}: wrong seller")
            if int(accepted.amount) != expected:
                raise RuntimeError(f"{tool}: wrong amount")
            if "bazaar" not in (required.extensions or {}):
                raise RuntimeError(f"{tool}: Bazaar extension missing")
    print(
        "all_unpaid=PASS; paid_tools=43; network=eip155:8453; "
        "asset=Base_USDC; seller=PASS; settlement_performed=false"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="https://1cent.maxzoa.ru")
    args = parser.parse_args()
    run(args.base_url.rstrip("/"))


if __name__ == "__main__":
    main()
