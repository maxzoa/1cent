# onecent-buyer

Safety-first local x402 buyer for `https://1cent.maxzoa.ru`.

```bash
npm ci
npm exec -- onecent-buyer doctor
```

This command uses the checked-out release package. Public npm publication is a separate release
step and is not assumed here.

`doctor` never pays. A paid `call` requires `--pay`, exact network, asset and seller
confirmations, `--confirm-charge PAY-ONCE`, and an atomic per-call cap. The buyer key stays in the
local process. Ambiguous outcomes are reported as `UNKNOWN` and are never retried automatically.
