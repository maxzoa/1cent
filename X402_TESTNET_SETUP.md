# x402 v2 testnet setup

> [!WARNING]
> **TESTNET-ONLY.** This file configures isolated Base Sepolia development. Public 1cent production
> runs on Base Mainnet; see [CURRENT_PRODUCTION.md](CURRENT_PRODUCTION.md). Never copy this profile
> over the production `.env`.

Pinned SDK: `x402[fastapi,httpx,evm,extensions]==2.16.0`.

- Network: Base Sepolia, `eip155:84532`.
- Facilitator: `https://x402.org/facilitator`.
- Asset: test USDC, `0x036CbD53842c5426634e7929541eC2318f3dCF7e`.
- Seller needs only public `X402_PAY_TO`; never store seller private key.
- Buyer is isolated and testnet-only. Private key exists only in `.env.test`, mode `600`.

Create buyer once:

```sh
cd /volume1/docker/1cent
docker compose run --rm --no-deps -v "$PWD:/work" -w /work onecent-api \
  python scripts/create_test_buyer_wallet.py
chmod 600 .env.test
```

Fund displayed buyer public address with Base Sepolia test USDC from an official faucet. Do not send mainnet assets.

Run real acceptance test:

```sh
cd /volume1/docker/1cent
./scripts/smoke_x402_testnet.sh https://1cent.maxzoa.ru
```

Development bypass works only from loopback, outside production, without Cloudflare headers, and never on host `1cent.maxzoa.ru`.
