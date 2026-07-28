# x402 payment flow

1. Send the strict JSON request without payment and inspect HTTP 402.
2. Pin version 2, `exact`, `eip155:8453`, Base USDC, amount, resource and seller.
3. Sign once with a unique payment identifier and submit once.
4. Treat an ambiguous response as UNKNOWN: never create a replacement identifier or retry automatically.
5. On success, retain `PAYMENT-RESPONSE` and the transaction hash.
