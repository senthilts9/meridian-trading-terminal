# Testnet Trading Terminal — Step 1/2 Validation

**Status: full lifecycle confirmed live on the exchange's testnet** (2026-07-24). Placed a
BUY MARKET/IOC order on BTC-USD-PERP, confirmed the fill, saw the position open with live
unrealized P&L, closed it with a reduce_only SELL, and confirmed it in trade history — all
against the real testnet API, not mocked. Full run: `lifecycle_report_20260724_071406.json`.

Validates the full testnet trade lifecycle end-to-end before any UI work starts:

```
Wallet -> Testnet funding -> Exchange account (onboarding) -> Market data
-> Place order -> Order accepted -> Trade executed -> Position opened
-> Monitor position/P&L -> Close position -> Trade history
```

Uses the exchange's official Python SDK rather than hand-rolled request signing, so the
auth/signature scheme always matches whatever the exchange currently implements (see "Why
the SDK, not raw REST" below).

## Setup

```bash
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate.bat for cmd
pip install -r requirements.txt
cp .env.example .env
```

### If you're behind a corporate SSL-inspecting proxy

`pip`/`requests` will fail with `CERTIFICATE_VERIFY_FAILED` if your network intercepts TLS
(common on corporate laptops). Fix, in order of preference:

1. Try `pip install pip-system-certs` first — it patches Python to trust the OS (Windows)
   certificate store automatically. Handles most cases.
2. If that's not enough (e.g. some subprocess build steps don't inherit it), export the
   Windows trust store to a PEM bundle and point env vars at it:
   ```powershell
   # See scripts in git history / ask for the export snippet used during setup —
   # exports Cert:\LocalMachine\Root + Cert:\LocalMachine\CA to corp-ca-bundle.pem
   ```
   then set `SSL_CERT_FILE` / `REQUESTS_CA_BUNDLE` in `.env` to that file's path.

### Python version note

`starknet-crypto-py` (a transitive dependency, Rust-based) only ships prebuilt Windows
wheels for **Python 3.10**. On 3.11+/3.13 it falls back to a from-source build requiring a
full MSVC C++ toolchain. Easiest fix: use Python 3.10 for this venv
(`winget install Python.Python.3.10`), not the system's newer Python.

## Step 1 — Wallet

```bash
python scripts/00_generate_wallet.py
```

Generates a fresh, disposable Ethereum keypair (never reused, never touches mainnet).
Copy the printed `L1_ADDRESS` / `L1_PRIVATE_KEY` into `.env`.

## Step 2 — Fund the wallet (required before onboarding)

The exchange's `/onboarding` endpoint rejects brand-new wallets with
`INSUFFICIENT_MIN_CHAIN_BALANCE` — an anti-Sybil safeguard. Your `L1_ADDRESS` needs
**at least 0.001 ETH or 5 USDC on Ethereum Sepolia, Arbitrum Sepolia, or Base** before
the SDK can onboard it. Get testnet ETH from:

- Google Cloud Web3 Faucet: `cloud.google.com/application/web3/faucet/ethereum/sepolia`
- Alchemy Sepolia Faucet: `sepoliafaucet.com`

Once funded, the exchange account itself is auto-credited **~$100,000 test USDC** on
first onboarding — no bridging or deposit step needed for trading capital itself; the
small L1 balance is purely the Sybil-resistance gate.

## Step 3 — Register a trading subkey (required — see bugs below)

```bash
python scripts/01_register_subkey.py
```

Copy the printed `MAIN_L2_ADDRESS` / `SUBKEY_L2_PRIVATE_KEY` into `.env`. This step exists
because of two live exchange-side issues discovered while building this — see
"Two exchange-side bugs found" below before assuming this is a normal SDK step.

## Step 4 — Run each lifecycle stage individually

```bash
python scripts/02_market_data.py      # public: markets, orderbook, BBO
python scripts/03_place_order.py      # place a BUY MARKET/IOC order
python scripts/04_check_order.py      # check order status
python scripts/05_check_fill.py       # check fills/executions
python scripts/06_position_pnl.py     # open position + account P&L
python scripts/07_close_position.py   # close with an opposite reduce_only order
python scripts/08_trade_history.py    # orders history, fills, transactions
```

## Step 5 — Or run the whole thing end-to-end

```bash
python scripts/run_full_lifecycle.py
```

Runs every stage in order, verifies each one before proceeding (order reached a terminal
state, position actually opened, position actually closed), and writes a full JSON report
to `lifecycle_report_<timestamp>.json` at the project root.

## Postman

`postman/Exchange_Testnet.postman_collection.json` covers the same endpoints:

- **Public folder** — market data, system info. Works out of the box, no auth.
- **Private folders** — account, positions, orders, fills, history. Need a bearer JWT.

Authentication is a SIWE (EIP-191) signature challenge, which Postman can't produce on its
own. Run `python scripts/get_jwt_for_postman.py` to mint a short-lived (~5 min) token and
paste it into the collection's `jwt_token` variable — enough to explore the private GET
endpoints interactively. Placing orders still needs a signed payload the SDK builds, so
that stays in `03_place_order.py` / `07_close_position.py`; the Postman order-placement
requests are documented but not directly runnable, to be upfront about that limitation.

## Two exchange-side bugs found, and how this project routes around them

**Bug 1 — the "native Starknet account" onboarding path is currently broken on testnet.**
The constructor shown in the SDK's own top-level example derives a Starknet account the
legacy way and tries to deploy it on-chain using the contract class in `system/config`'s
`paraclear_account_proxy_hash`. That class
(`0x03530cc4759d78042f1b543bf797f5f3d647cde0388c33734cf91b7f7b9314a9`) is **not declared**
on the exchange's testnet chain right now — confirmed directly via `starknet_getClass`
against the testnet RPC endpoint, independent of any SDK version (checked against the
latest release on PyPI). Every deploy attempt via this path reverts with `Class ... is not
declared`. This blocks *any* new account trying to onboard this way, not just this
project's wallet.

**Workaround:** the EVM/SIWE auth path uses a *different* declared class
(`paraclear_evm_account_hash`) and worked cleanly — account created, `$100,001` test USDC
credited, deploy tx `PRE_CONFIRMED` (not reverted). This is why `config.py` uses that path
for onboarding instead of the legacy native-account constructor.

**Bug 2 — the SDK's subkey-registration helper is broken against the live API.** An
EVM-authenticated account has no Starknet signing key of its own, so it can't sign orders
— the fix is registering a "subkey" (a real Starknet keypair) for order signing. The SDK's
convenience helper for this omits fields the server now requires
(`INVALID_REQUEST_PARAMETER: evm_signature is required for EIP-191 accounts`) — confirmed
against both the released package and the current GitHub `main` branch, so it's not yet
fixed upstream either.

**Workaround:** `scripts/01_register_subkey.py` builds the required SIWE message by hand
(`Statement` must read `Subkey Registration: 0x<pubkey>`, lowercased, plus an
`Expiration Time` line — both undocumented in the SDK, found by iterating on the API's
error messages) and calls the low-level subkey-creation method directly, bypassing the
broken helper. The resulting subkey is fully functional (`can_trade: True`) and is what
`config.py`'s `get_authenticated_client()` actually uses.

Net effect: this project never had to wait on the exchange to fix Bug 1 — the whole
lifecycle runs on the EVM/SIWE client (onboarding/reads) + a hand-registered subkey client
(trading), entirely within the SDK's public API surface, just not the paths its own docs
lead with.

## Why the SDK, not raw REST

An earlier reference doc (a documentation mockup) suggested hand-signing orders with a
raw Starknet Pedersen-hash scheme. Live testing against the current API showed the real
flow is EIP-191/SIWE-based, and the exact market config field names differ too
(`order_size_increment`/`price_tick_size`, not `step_size`/`tick_size`). Building on the
official SDK avoids silently drifting from whatever the exchange's API actually does today.

## Step 3 — the UI (built and verified)

```
React (Vite + TS, dark theme) -> FastAPI (backend/) -> Exchange SDK -> Exchange Testnet
```

Built and confirmed working end-to-end via headless-browser interaction (place order ->
position opens live -> close position -> flat, all through the actual UI):

- **`backend/`** — FastAPI wrapper around the same exchange client used above (imports
  `scripts/config.py` directly, one source of truth for auth). REST for
  markets/account/positions/orders/fills, a WebSocket at `/ws/{market}` streaming
  BBO + account + positions every 2s.
- **`frontend/`** — Vite + React + TypeScript dark-themed dashboard: market ticker, order
  ticket, positions table with a Close button, open orders, order history, fills.
  Author credit in the footer.

Run: `cd backend && uvicorn main:app --reload --port 8000`, then
`cd frontend && npm run dev` → http://localhost:5173. Full details, architecture, and
screenshots: `docs/RUNBOOK.md`.

## Bonus — CMLE: independent risk model (C++, standalone)

`quant-cpp/` is a standalone C++ tool ("Meridian Risk Model") that independently computes
an estimated liquidation price from first principles, for comparison against whatever the
exchange itself reports — validated at **0.0456% relative error** against a real captured
position. Deliberately decoupled from the live app (no network calls, not wired into the
backend) — a portfolio artifact demonstrating the model, not a production dependency.
See `quant-cpp/README.md` for the derivation, validation, and usage.
