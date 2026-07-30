#!/usr/bin/env node
import { pathToFileURL } from "node:url";

const BASE = "https://1cent.maxzoa.ru";
export const NETWORK = "eip155:8453";
export const ASSET = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913";
export const SELLER = "0x4798e8401ba3b1566685257c82d06303AB90EA35";

export function options(argv) {
  const parsed = { command: argv[0] || "help" };
  for (let index = 1; index < argv.length; index += 1) {
    const key = argv[index];
    if (!key.startsWith("--")) throw new Error(`unexpected argument: ${key}`);
    const next = argv[index + 1];
    if (!next || next.startsWith("--")) parsed[key.slice(2)] = true;
    else {
      parsed[key.slice(2)] = next;
      index += 1;
    }
  }
  return parsed;
}

export function validatePayment(opts, amount) {
  if (opts.pay !== true) throw new Error("payment disabled: add --pay");
  if (opts["confirm-network"] !== NETWORK) throw new Error("network confirmation mismatch");
  if (opts["confirm-asset"]?.toLowerCase() !== ASSET.toLowerCase()) {
    throw new Error("asset confirmation mismatch");
  }
  if (opts["confirm-seller"]?.toLowerCase() !== SELLER.toLowerCase()) {
    throw new Error("seller confirmation mismatch");
  }
  if (opts["confirm-charge"] !== "PAY-ONCE") throw new Error("charge confirmation mismatch");
  const cap = BigInt(opts["max-atomic"] || "0");
  if (cap <= 0n || BigInt(amount) > cap) throw new Error("price exceeds explicit cap");
  return cap;
}

async function doctor(opts) {
  const base = opts["base-url"] || BASE;
  const response = await fetch(`${base}/v1/url/status`, {
    method: "POST",
    headers: {"content-type": "application/json", "user-agent": "onecent-buyer-npm/0.7"},
    body: JSON.stringify({url: "https://example.com/", fresh: false}),
  });
  console.log(JSON.stringify({ready: response.status === 402, httpStatus: response.status,
    paymentExecuted: false, paymentRequired: response.headers.has("payment-required")}, null, 2));
  return response.status === 402 ? 0 : 1;
}

async function call(opts) {
  const quote = await fetch(`${opts["base-url"] || BASE}${opts.endpoint || "/v1/url/status"}`, {
    method: "POST", headers: {"content-type": "application/json"},
    body: JSON.stringify({url: opts.url || "https://example.com/", fresh: false}),
  });
  const encoded = quote.headers.get("payment-required");
  if (quote.status !== 402 || !encoded) throw new Error("valid 402 challenge not received");
  const required = JSON.parse(Buffer.from(encoded, "base64url").toString("utf8"));
  const accepted = required.accepts?.[0];
  if (!accepted) throw new Error("challenge has no payment option");
  validatePayment(opts, accepted.amount);
  const privateKey = process.env.ONECENT_BUYER_PRIVATE_KEY;
  if (!privateKey) throw new Error("ONECENT_BUYER_PRIVATE_KEY is not configured");
  const [{wrapFetchWithPaymentFromConfig}, {ExactEvmScheme}, {privateKeyToAccount}] =
    await Promise.all([import("@x402/fetch"), import("@x402/evm/exact/client"), import("viem/accounts")]);
  const paidFetch = wrapFetchWithPaymentFromConfig(fetch, {
    schemes: [{network: NETWORK, client: new ExactEvmScheme(privateKeyToAccount(privateKey))}],
    paymentRequirementsSelector: (_version, accepts) => {
      const matches = accepts.filter((item) => item.scheme === "exact" &&
        item.network === NETWORK && item.asset.toLowerCase() === ASSET.toLowerCase() &&
        item.payTo.toLowerCase() === SELLER.toLowerCase() &&
        BigInt(item.amount) <= BigInt(opts["max-atomic"]));
      if (matches.length !== 1) throw new Error("no single exact payment option matches policy");
      return matches[0];
    },
  });
  try {
    const response = await paidFetch(`${opts["base-url"] || BASE}${opts.endpoint || "/v1/url/status"}`, {
      method: "POST", headers: {"content-type": "application/json"},
      body: JSON.stringify({url: opts.url || "https://example.com/", fresh: false}),
    });
    console.log(JSON.stringify({status: response.status === 200 ? "SUCCESS" : "FAILED",
      httpStatus: response.status, requestId: response.headers.get("x-request-id"),
      paymentResponse: response.headers.has("payment-response"), result: await response.json()}, null, 2));
    return response.status === 200 ? 0 : 1;
  } catch (error) {
    console.error(JSON.stringify({status: "UNKNOWN", automaticRetry: false,
      error: error.constructor.name}));
    return 2;
  }
}

export async function main(argv = process.argv.slice(2)) {
  const opts = options(argv);
  if (opts.command === "doctor") return doctor(opts);
  if (opts.command === "call") return call(opts);
  console.log("Usage: onecent-buyer doctor | call [explicit payment confirmations]");
  return opts.command === "help" ? 0 : 1;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  main().then((code) => { process.exitCode = code; }).catch((error) => {
    console.error(`BLOCKED: ${error.message}`); process.exitCode = 1;
  });
}
