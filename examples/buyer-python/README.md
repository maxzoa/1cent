# Python buyer

This official-SDK example performs at most one request and caps the accepted price at
`1000` atomic USDC (`0.001 USDC`). The private key stays in the buyer process.

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
ONECENT_BUYER_PRIVATE_KEY=0x... .venv/bin/python buyer.py
```

Run `onecent doctor` first. Never place a key in source control or command history.
