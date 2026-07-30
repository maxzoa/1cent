from __future__ import annotations

import asyncio
import json
import math
from typing import Any

import httpx

BASE_URL = "https://1cent.maxzoa.ru"
CATALOG_URL = f"{BASE_URL}/v1/catalog"
DISCOVERY_URL = "https://facilitator.payai.network/discovery/resources"
SUPPORTED_URL = "https://facilitator.payai.network/supported"
PAGE_SIZE = 100


def _flatten(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


async def _page(
    client: httpx.AsyncClient, semaphore: asyncio.Semaphore, offset: int
) -> list[dict[str, Any]]:
    async with semaphore:
        response = await client.get(
            DISCOVERY_URL,
            params={"limit": PAGE_SIZE, "offset": offset},
        )
        response.raise_for_status()
    items = response.json().get("items", [])
    if not isinstance(items, list):
        raise TypeError("PayAI discovery items must be a list")
    return [item for item in items if isinstance(item, dict)]


async def main() -> None:
    timeout = httpx.Timeout(60.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        catalog_response, supported_response, first_response = await asyncio.gather(
            client.get(CATALOG_URL),
            client.get(SUPPORTED_URL),
            client.get(DISCOVERY_URL, params={"limit": PAGE_SIZE, "offset": 0}),
        )
        catalog_response.raise_for_status()
        supported_response.raise_for_status()
        first_response.raise_for_status()

        catalog = catalog_response.json()
        if not isinstance(catalog, list):
            raise TypeError("1cent catalog must be a list")
        expected = {
            f"{BASE_URL}{item['rest_path']}"
            for item in catalog
            if isinstance(item, dict) and isinstance(item.get("rest_path"), str)
        }

        first = first_response.json()
        pagination = first.get("pagination", {})
        total = int(pagination.get("total", 0))
        first_items = first.get("items", [])
        if not isinstance(first_items, list):
            raise TypeError("PayAI discovery items must be a list")

        offsets = range(PAGE_SIZE, math.ceil(total / PAGE_SIZE) * PAGE_SIZE, PAGE_SIZE)
        semaphore = asyncio.Semaphore(12)
        remaining_pages = await asyncio.gather(
            *(_page(client, semaphore, offset) for offset in offsets)
        )
        all_items = [*first_items, *(item for page in remaining_pages for item in page)]
        onecent_documents = [
            _flatten(item) for item in all_items if "1cent.maxzoa.ru" in _flatten(item)
        ]
        present = {
            url for url in expected if any(url in document for document in onecent_documents)
        }
        missing = sorted(expected - present)

        supported_text = _flatten(supported_response.json()).lower()
        required_capabilities = ("eip155:8453", "exact", "bazaar")
        capability_pass = all(value in supported_text for value in required_capabilities)

    print(
        "payai_bazaar_readonly=" + ("PASS" if not missing and capability_pass else "FAIL")
    )
    print(f"catalog_expected={len(expected)}; bazaar_present={len(present)}")
    print(f"payai_total_resources={total}; onecent_documents={len(onecent_documents)}")
    print(f"supported_capabilities={'PASS' if capability_pass else 'FAIL'}")
    if missing:
        print("missing=" + ",".join(missing))


if __name__ == "__main__":
    asyncio.run(main())
