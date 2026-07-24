# Paradex Testnet Trading Bot — Runbook & Architecture

**Author:** Senthil Saravanamuthu
**Status:** Full trade lifecycle verified live on Paradex testnet (2026-07-24)

This document is for anyone picking up this project cold — what it does, why it's built
this way, every API endpoint it touches and why, and how to run it yourself.

---

## 1. What this project proves

A complete, automated crypto perpetuals trade lifecycle against Paradex's testnet, using
a self-custodial wallet with no manual browser trading:

```
Self-custodial wallet (generated, testnet-only)
        |
        v
Fund with testnet ETH (Sepolia faucet — anti-Sybil gate, not trading capital)
        |
        v
Paradex account (SIWE onboarding) ---> auto-credited ~$100,000 test USDC
        |
        v
Register a trading subkey (Starknet keypair, API-registered — see Section 5, Bug 2)
        |
        v
Read live market data (orderbook, BBO, mark price)
        |
        v
Place order (signed by the subkey) ---> matched by Paradex's engine
        |
        v
Confirm fill ---> Position opens ---> Monitor unrealized P&L
        |
        v
Close position (opposite reduce_only order) ---> Confirm flat
        |
        v
Trade history (orders, fills, transactions) — audit trail
```

Every arrow above is a real HTTP call to `api.testnet.paradex.trade`, not a mock.

---

## 2. Architecture

### 2.1 Current state (Step 1/2 — validated)

```
+------------------------------------------------------------------+
|                     Your machine (this repo)                     |
|                                                                    |
|  scripts/*.py  --uses-->  paradex_py SDK  --HTTPS-->  Paradex API |
|       |                                                testnet    |
|       v                                                            |
|   .env (wallet + subkey, gitignored)                              |
|   logs/ (run logs)                                                 |
|   lifecycle_report_*.json (evidence per run)                      |
+------------------------------------------------------------------+
```

Two client identities are used, deliberately (see Section 5 for why there are two):

| Client | Class | Can read account/positions/orders? | Can sign orders? | Can withdraw? |
|---|---|---|---|---|
| Main account | `ParadexEvm` (SIWE/EIP-191) | Yes | **No** | Yes |
| Trading subkey | `ParadexSubkey` | Yes | **Yes** | No |

The main account authenticates with your Ethereum wallet signature (SIWE) — it owns the
funds and can register/revoke subkeys, but has no Starknet private key to sign orders
with. The subkey is a separate, disposable Starknet keypair registered *to* the main
account specifically for order signing, so the Ethereum private key never has to touch
order-signing logic. This is Paradex's actual security model, not a shortcut we invented.

### 2.2 Planned state (Step 3 — UI, next)

```
React/Vite dark-themed UI  <-- REST/WS -->  FastAPI backend  <-- REST/WS -->  Paradex testnet
     (browser, public)                    (holds wallet/subkey,
                                            never exposed to browser)
```

The FastAPI backend is the only thing that ever holds the private keys; the browser talks
only to our backend, never directly to Paradex, and never sees a private key.

---

## 3. Every endpoint used, and why

All base URLs: `https://api.testnet.paradex.trade/v1` unless noted.

### 3.1 Public — no authentication

| Endpoint | Method | Purpose | Used in |
|---|---|---|---|
| `/system/state` | GET | Health check — is the API up | connectivity smoke test |
| `/system/time` | GET | Server clock — needed to keep signed timestamps in sync | `config.py` (indirect, via SDK) |
| `/system/config` | GET | Chain addresses, contract class hashes, bridged token list, L1 chain ID. This is the config that revealed Bug 1 (see Section 5) | every client init |
| `/markets?market=X` | GET | Static contract spec for a market: tick size, min order size, min notional, max leverage. Needed to size orders correctly | `02_market_data.py`, `03_place_order.py` |
| `/markets/summary?market=X` | GET | Live 24h stats: mark price, bid/ask, funding rate, volume | `02_market_data.py`, `03_place_order.py` (for sizing) |
| `/orderbook/{market}` | GET | L2 order book snapshot (bids/asks with depth) | `02_market_data.py` |
| `/bbo/{market}` | GET | Best bid/offer only — cheaper than full orderbook when you just need the touch price | `02_market_data.py` |
| `/trades?market=X` | GET | Public trade tape (recent executions, anonymized) | Postman public folder |

### 3.2 Authentication

| Endpoint | Method | Purpose | Notes |
|---|---|---|---|
| `/v2/onboarding` | POST | Register a new EVM (SIWE) account. One-time per wallet, idempotent | Requires the wallet hold ≥0.001 ETH or 5 USDC on Sepolia/Arbitrum/Base first (anti-Sybil gate) |
| `/v2/auth` | POST | Exchange a SIWE signature for a JWT bearer token (short-lived, ~5 min, auto-refreshed by the SDK) | Used before every private call |
| `/onboarding` (legacy) | POST | Native-Starknet-key onboarding | **Currently broken on testnet — see Bug 1.** Kept in the doc so nobody rediscovers this the hard way |
| `/auth/{pubkey}` (legacy) | POST | Native-Starknet-key auth | Same legacy path, same bug exposure |

### 3.3 Private — Account

| Endpoint | Method | Purpose | Used in |
|---|---|---|---|
| `/account` | GET | Full margin snapshot: account value, free collateral, initial/maintenance margin requirement, status (`ACTIVE`/`LIQUIDATING`) | `06_position_pnl.py`, every lifecycle stage as a checkpoint |
| `/balance` | GET | Per-asset balances (USDC, etc.) | onboarding verification |
| `/positions` | GET | All open positions: size, side, entry/mark price, unrealized P&L, liquidation price | `06_position_pnl.py`, `07_close_position.py` |

### 3.4 Private — Subkey management

| Endpoint | Method | Purpose | Used in |
|---|---|---|---|
| `/account/keys/subkeys` | GET | List subkeys registered to this account | debugging |
| `/account/keys/subkeys` | POST | Register a new subkey for order signing. **Requires `evm_signature` + `siwe_message` fields for EVM accounts — the SDK's own helper omits these; see Bug 2** | `01_register_subkey.py` |

### 3.5 Private — Orders

| Endpoint | Method | Purpose | Used in |
|---|---|---|---|
| `/orders` | POST | Place an order (signed by the subkey). We use `MARKET` + `IOC` (immediate-or-cancel) so the lifecycle test never leaves a resting order behind | `03_place_order.py` |
| `/orders/{id}` | GET | Check a specific order's status/fill progress | `04_check_order.py`, lifecycle runner's terminal-state poll |
| `/orders/by_client_id/{client_id}` | GET | Same, looked up by our own idempotency key instead of Paradex's order id | `04_check_order.py` |
| `/orders` | GET | List currently open orders | `04_check_order.py` |
| `/orders-history` | GET | Historical (closed/cancelled) orders | `08_trade_history.py` |
| `/orders/{id}` | DELETE | Cancel a resting order | available, not needed (we only use IOC orders) |

### 3.6 Private — Fills & transactions

| Endpoint | Method | Purpose | Used in |
|---|---|---|---|
| `/fills` | GET | Execution records: price, size, fee, realized P&L per fill | `05_check_fill.py`, `08_trade_history.py` |
| `/transactions` | GET | On-chain-settled account transactions (account deploy, fills, transfers) — this is what revealed the `REVERTED` account-deploy transaction in Bug 1 | `08_trade_history.py`, Bug 1 investigation |

---

## 4. How to run this yourself

```bash
cd paradex-trading-bot
python -m venv venv                 # use Python 3.10 — see README's "Python version note"
source venv/Scripts/activate
pip install -r requirements.txt
cp .env.example .env

python scripts/00_generate_wallet.py         # generates L1_ADDRESS/L1_PRIVATE_KEY -> paste into .env
#  --> fund L1_ADDRESS with Sepolia ETH via a faucet (see README Step 2) --
python scripts/01_register_subkey.py         # generates MAIN_L2_ADDRESS/SUBKEY_L2_PRIVATE_KEY -> paste into .env

python scripts/run_full_lifecycle.py         # runs the entire lifecycle, writes logs/ + a JSON report
```

Every run appends a timestamped log file to `logs/` and a `lifecycle_report_<timestamp>.json`
snapshot at the project root — both are the evidence trail for "did this actually work,"
not just "did it look like it worked."

---

## 5. Two Paradex-side bugs found (read before debugging auth failures yourself)

Full technical detail is in the main `README.md`; summarized here for the runbook:

1. **Legacy native-Starknet onboarding is broken on testnet right now.** The account-deploy
   transaction reverts because the contract class Paradex's own `/system/config` tells
   clients to deploy (`paraclear_account_proxy_hash`) isn't declared on their chain.
   Confirmed via direct RPC query (`starknet_getClass`), independent of SDK version.
2. **The SDK's `ParadexEvm.create_trading_subkey()` helper is broken against the live API**
   — it omits the `evm_signature`/`siwe_message` fields the server now requires for
   EIP-191 accounts. Confirmed against both the released package and GitHub `main`.

This project routes around both (see `scripts/config.py` and `scripts/01_register_subkey.py`)
by using `ParadexEvm` + a hand-registered `ParadexSubkey` instead of the paths the SDK's
own top-level examples lead with.

---

## 6. Step 3 — the UI (built, verified working)

```
React (Vite + TS, dark theme)  <--REST + WS-->  FastAPI (backend/)  <--REST-->  Paradex testnet
```

The backend (`backend/main.py`) is a thin wrapper: every endpoint just calls the same
`paradex_py` client used by the scripts (imported directly from `scripts/config.py`, so
there's one source of truth for auth). It exposes REST endpoints for markets, account,
positions, orders (place/history), and fills, plus a `/ws/{market}` WebSocket that pushes
BBO + account + positions every 2s so the UI updates live without polling.

The frontend (`frontend/`) is a Vite + React + TypeScript dashboard: market ticker with
live bid/ask, account panel (value/margin/free collateral), an order ticket (buy/sell,
market or limit), an open-positions table with a one-click Close button, open orders,
order history, and fills — all real data, no mocks.

**Run both:**

```bash
# Terminal 1 -- backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 2 -- frontend
cd frontend
npm install
npm run dev   # http://localhost:5173
```

**Verified end-to-end via headless-browser interaction** (not just "it compiles"): loaded
the dashboard, clicked Buy, watched the position open live with real unrealized P&L,
clicked Close, watched it flatten — all through the actual UI, zero console errors.
Screenshots: `docs/screenshots/dashboard-overview.png`,
`dashboard-position-open.png`, `dashboard-position-closed.png`.

Note on the WebSocket relay: `/ws/{market}` is a polling relay (fetches BBO/account/positions
every 2s and pushes the snapshot), not a direct bridge to Paradex's own WS channel protocol.
This was the pragmatic choice for a v1 — correct data, simple to reason about — rather than
implementing Paradex's native WS subscription/SBE handling. A closer-to-the-metal version
would subscribe to Paradex's WS channels directly and relay ticks as they arrive instead of
polling; worth doing if latency matters for a real strategy.
