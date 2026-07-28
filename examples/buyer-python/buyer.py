"""One explicitly capped x402 call. Review `onecent doctor` first."""

import asyncio
import os

from eth_account import Account
from x402 import x402Client
from x402.client import max_amount
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

MAX_ATOMIC_USDC = 1_000  # Hard cap: 0.001 USDC.


async def main() -> None:
    account = Account.from_key(os.environ["ONECENT_BUYER_PRIVATE_KEY"])
    client = x402Client().register_policy(max_amount(MAX_ATOMIC_USDC))
    register_exact_evm_client(client, EthAccountSigner(account))
    async with x402HttpxClient(client, timeout=30, follow_redirects=False) as http:
        response = await http.post(
            "https://1cent.maxzoa.ru/v1/url/status",
            json={"url": "https://example.com/", "fresh": False},
        )
        await response.aread()
    print(response.status_code, response.headers.get("X-Request-ID"))
    print(response.json())


if __name__ == "__main__":
    asyncio.run(main())
