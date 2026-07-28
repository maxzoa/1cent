# Node.js buyer

This official-SDK example performs at most one request and refuses prices above `0.001 USDC`.
The dependency versions are pinned. The private key stays in the buyer process.

```bash
npm ci
ONECENT_BUYER_PRIVATE_KEY=0x... npm start
```

Run `onecent doctor` first. Never commit the key.
