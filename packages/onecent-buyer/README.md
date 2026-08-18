# onecent-buyer

Safety-first local x402 buyer for `https://1cent.maxzoa.ru`.

```bash
npm install --global onecent-buyer@0.8.1
onecent-buyer doctor
```

The public package is available at
[npm `onecent-buyer` 0.8.1](https://www.npmjs.com/package/onecent-buyer/v/0.8.1). Contributors can
still run `npm ci && npm exec -- onecent-buyer doctor` from this directory.

`doctor` never pays. A paid `call` requires `--pay`, exact network, asset and seller
confirmations, `--confirm-charge PAY-ONCE`, and an atomic per-call cap. The buyer key stays in the
local process. Ambiguous outcomes are reported as `UNKNOWN` and are never retried automatically.
