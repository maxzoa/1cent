import { wrapFetchWithPaymentFromConfig } from "@x402/fetch";
import { ExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const privateKey = process.env.ONECENT_BUYER_PRIVATE_KEY;
if (!privateKey) throw new Error("ONECENT_BUYER_PRIVATE_KEY is required");

const MAX_ATOMIC_USDC = 1000n; // Hard cap: 0.001 USDC.
const signer = privateKeyToAccount(privateKey);
const paidFetch = wrapFetchWithPaymentFromConfig(fetch, {
  schemes: [{ network: "eip155:8453", client: new ExactEvmScheme(signer) }],
  paymentRequirementsSelector: (_version, accepts) => {
    const exactBase = accepts.filter(
      (item) =>
        item.scheme === "exact" &&
        item.network === "eip155:8453" &&
        BigInt(item.amount) <= MAX_ATOMIC_USDC,
    );
    if (exactBase.length !== 1) throw new Error("No single safe payment option under cap");
    return exactBase[0];
  },
});

const response = await paidFetch("https://1cent.maxzoa.ru/v1/url/status", {
  method: "POST",
  headers: { "content-type": "application/json" },
  body: JSON.stringify({ url: "https://example.com/", fresh: false }),
});
console.log(response.status, response.headers.get("X-Request-ID"));
console.log(await response.json());
