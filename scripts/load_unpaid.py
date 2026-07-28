import argparse
import asyncio
import json
from statistics import mean
from time import monotonic

import httpx


async def main() -> int:
    parser = argparse.ArgumentParser(description="No-payment 402 load smoke")
    parser.add_argument("--base-url", default="http://127.0.0.1:8013")
    parser.add_argument("--requests", type=int, default=25)
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args()
    if not 1 <= args.requests <= 200 or not 1 <= args.concurrency <= 10:
        raise SystemExit("safe limits: requests 1..200, concurrency 1..10")
    semaphore = asyncio.Semaphore(args.concurrency)
    latencies: list[float] = []

    async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
        async def probe() -> None:
            async with semaphore:
                started = monotonic()
                response = await client.post(
                    f"{args.base_url.rstrip('/')}/v1/url/status",
                    json={"url": "https://example.com/", "fresh": False},
                    headers={"User-Agent": "onecent-smoke/unpaid-load"},
                )
                latencies.append((monotonic() - started) * 1000)
                if response.status_code != 402 or not response.headers.get("PAYMENT-REQUIRED"):
                    raise RuntimeError(f"unexpected response: {response.status_code}")

        await asyncio.gather(*(probe() for _ in range(args.requests)))
    ordered = sorted(latencies)
    p95 = ordered[max(0, ((len(ordered) * 95 + 99) // 100) - 1)]
    print(
        json.dumps(
            {
                "result": "PASS",
                "payment_executed": False,
                "requests": len(ordered),
                "concurrency": args.concurrency,
                "average_ms": round(mean(ordered), 1),
                "p95_ms": round(p95, 1),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
