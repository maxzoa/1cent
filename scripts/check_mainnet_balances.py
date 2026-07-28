import argparse
import asyncio

import httpx

BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"


def has_minimum_usdc(balance_atomic: int, minimum_atomic: int) -> bool:
    return balance_atomic >= minimum_atomic


async def rpc(client: httpx.AsyncClient, method: str, params: list[object]) -> str:
    response = await client.post(
        "https://mainnet.base.org",
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
    )
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        raise RuntimeError(f"RPC {method} failed")
    return str(data["result"])


async def token_balance(client: httpx.AsyncClient, address: str) -> int:
    data = "0x70a08231" + address.lower().removeprefix("0x").rjust(64, "0")
    result = await rpc(client, "eth_call", [{"to": BASE_USDC, "data": data}, "latest"])
    return int(result, 16)


async def run(buyer: str, seller: str, minimum_buyer_usdc_atomic: int | None) -> None:
    async with httpx.AsyncClient(timeout=20.0) as client:
        buyer_usdc = await token_balance(client, buyer)
        seller_usdc = await token_balance(client, seller)
        buyer_eth = int(await rpc(client, "eth_getBalance", [buyer, "latest"]), 16)
    print(f"buyer={buyer}")
    print(f"buyer_usdc={buyer_usdc / 1_000_000:.6f}")
    print(f"buyer_eth={buyer_eth / 10**18:.18f}")
    print(f"seller_usdc={seller_usdc / 1_000_000:.6f}")
    if minimum_buyer_usdc_atomic is not None:
        if not has_minimum_usdc(buyer_usdc, minimum_buyer_usdc_atomic):
            raise SystemExit(
                "BLOCKER: buyer USDC below minimum: "
                f"have={buyer_usdc} required={minimum_buyer_usdc_atomic} atomic"
            )
        print(
            "buyer_usdc_gate=PASS; "
            f"balance_atomic={buyer_usdc}; minimum_atomic={minimum_buyer_usdc_atomic}"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--buyer", required=True)
    parser.add_argument("--seller", required=True)
    parser.add_argument("--minimum-buyer-usdc-atomic", type=int)
    args = parser.parse_args()
    asyncio.run(run(args.buyer, args.seller, args.minimum_buyer_usdc_atomic))


if __name__ == "__main__":
    main()
