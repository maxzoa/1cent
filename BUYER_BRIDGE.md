# 1cent Buyer Bridge

Local stdio MCP server that lets payment-capable agents use 1cent without sending a buyer key to
1cent, an MCP directory or a remote MCP server. The bridge reads the live HTTP 402 challenge,
validates it, signs locally and submits one paid REST request through the official x402 Python SDK.

Remote production remains `https://1cent.maxzoa.ru/mcp`. The bridge is an optional buyer-side
adapter for MCP clients that can call tools but cannot create x402 payments themselves.

## Safety model

- Default mode is manual: every paid tool call returns a quote first and performs no payment.
- User approves exactly one quoted call with `onecent approve ... --confirm-charge PAY-ONCE`.
- Base Mainnet `eip155:8453`, Base USDC, seller, `exact`, resource URL and amount are pinned.
- Per-call and UTC-day spend caps are local buyer limits, not seller commercial quotas.
- Pending and UNKNOWN amounts consume the local daily cap.
- UNKNOWN outcome blocks the same request fingerprint; no automatic payment retry.
- A successful result requires HTTP 200 and `PAYMENT-RESPONSE`.
- Wallet secret is stored in the operating-system keyring or supplied by a headless process env.
- SQLite state stores approvals, caps and outcomes only. It never stores keys or signatures.

## Install

Requires Python 3.12+ and `pipx`:

```bash
pipx install "onecent[buyer]==0.8.0"
onecent wallet set
onecent wallet status
onecent doctor
```

The published package is available at
[PyPI `onecent` 0.8.0](https://pypi.org/project/onecent/0.8.0/). GitHub installation is reserved for
contributors testing unreleased changes.

Generate a client configuration without secrets:

```bash
onecent install --client claude
onecent install --client cursor --apply
onecent install --client vscode --apply
onecent install --client codex
```

`--apply` backs up an existing JSON file before editing it. Codex prints its exact CLI command and
does not edit configuration automatically.

`onecent wallet set` reads the key through a hidden terminal prompt and saves it using Windows
Credential Locker, macOS Keychain or the configured Linux keyring backend. Never put a key in MCP
JSON/TOML, source code, shell history, chat or a directory listing.

Headless agents may inject `ONECENT_BUYER_PRIVATE_KEY` into the local bridge process from their
existing secret manager. Environment injection overrides keyring lookup. 1cent never receives it.

## Manual mode — recommended first setup

Generic stdio command:

```bash
onecent bridge --max-usdc-per-call 0.001 --daily-limit-usdc 0.01
```

Generic Claude Desktop/Cursor-style configuration:

```json
{
  "mcpServers": {
    "1cent-buyer": {
      "command": "onecent",
      "args": [
        "bridge",
        "--max-usdc-per-call", "0.001",
        "--daily-limit-usdc", "0.01"
      ]
    }
  }
}
```

VS Code uses the same command and arguments under the top-level `servers` object in its user or
workspace `mcp.json`.

Codex CLI:

```bash
codex mcp add 1cent-buyer -- onecent bridge \
  --max-usdc-per-call 0.001 \
  --daily-limit-usdc 0.01
codex mcp list
```

Equivalent Codex `~/.codex/config.toml`:

```toml
[mcp_servers.1cent-buyer]
command = "onecent"
args = [
  "bridge",
  "--max-usdc-per-call", "0.001",
  "--daily-limit-usdc", "0.01",
]
default_tools_approval_mode = "prompt"
tool_timeout_sec = 90
```

Do not add the remote `https://1cent.maxzoa.ru/mcp` and local bridge simultaneously under the same
tool set: clients may show duplicate names and choose the non-paying remote path.

## First paid call

1. Ask the agent to call `buyer_bridge_status`.
2. Call free `catalog_search` or `demo_url_pulse`.
3. Ask for one paid tool, for example `url_status` for `https://example.com/`.
4. Bridge performs only an unpaid 402 quote and returns `PAYMENT_APPROVAL_REQUIRED`.
5. Review tool, amount, network and shortened seller. Run the exact returned `onecent approve`
   command.
6. Tell the agent to repeat the same tool call once.
7. Accept delivery only when bridge returns `payment.status=settled`.

Approval expires after ten minutes and is bound to exact tool, input, amount, network, asset,
seller and resource. Changed price or arguments require a new quote.

For `batch_url_status`, the bridge validates one to five distinct URLs and binds approval to the
whole ordered input. The approved amount is the live per-URL quote multiplied by URL count. An
ambiguous result blocks that exact fingerprint and never creates a replacement payment ID.

## Capped automatic mode — explicit opt-in

Manual mode is default. Headless agents may enable automatic payment only with every gate:

```bash
onecent bridge \
  --max-usdc-per-call 0.001 \
  --daily-limit-usdc 0.01 \
  --auto-pay \
  --confirm-network eip155:8453 \
  --confirm-asset 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 \
  --confirm-seller 0x4798e8401ba3b1566685257c82d06303AB90EA35 \
  --confirm-charge ALLOW-CAPPED-PAYMENTS
```

Missing or wrong gate aborts startup. The local daily limit is never unlimited and cannot be set to
zero. Choose caps independently from current promotional prices because live 402 remains the source
of truth.

## Recovery

```bash
onecent bridge-state
onecent wallet status
```

If `unresolved` is nonzero, do not repeat that request. Check chain receipt, seller balance and
server evidence using the returned request ID. Local state is intentionally not auto-reconciled.
Delete the wallet only when intended:

```bash
onecent wallet delete --confirm-delete DELETE-WALLET
```

## Finite recurring change checks

`onecent watch` calls the existing `url_changed` service; it is not a second payment path. It is
disabled until the buyer supplies `--execute`, `ALLOW-CAPPED-WATCH`, exact Base Mainnet
network/asset/seller confirmations and local per-call/day caps. Interval is at least 300 seconds,
run count is finite, and any UNKNOWN stops the process without retry.

## No-payment smoke

```bash
python scripts/smoke_buyer_bridge.py
python scripts/smoke_buyer_bridge.py --public
```

The public smoke initializes stdio MCP, checks all strict tool schemas, obtains one live 402 quote
and stops before approval/signing. It removes `ONECENT_BUYER_PRIVATE_KEY` from the child process.
