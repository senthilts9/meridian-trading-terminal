# LinkedIn post draft

Two versions — pick based on whether you want to name the exchange. Both are true; the
technical substance (bugs found, stack, lifecycle) doesn't change either way.

---

## Version A — names the exchange (shows real-integration credibility)

🚀 Built a full-stack crypto perpetuals trading terminal from scratch — wallet to UI.

**Meridian** is a self-custodial trading terminal I built end-to-end against Paradex's
testnet: Python + FastAPI backend, React/TypeScript dark-themed frontend, live WebSocket
market data, and a complete order lifecycle — place, fill, open position, live P&L, close,
trade history.

A few things that made this more than a weekend CRUD app:

🔧 Diagnosed and routed around **two live bugs in the exchange's own testnet
infrastructure** — a broken account-deployment path (traced to an undeclared Starknet
contract class via direct RPC queries) and a broken SDK helper missing a required
signature field. Found workarounds for both without waiting on an upstream fix.

🔐 Implemented the real self-custodial flow: generated a fresh wallet, funded it on
Sepolia testnet, onboarded via SIWE (Sign-In with Ethereum), and registered a scoped
trading subkey — the same security model real self-custodial exchanges use, not a
simplified mock.

📊 Full observability: every API call logged, every trade lifecycle run produces a
timestamped evidence report — because "it works on my machine" isn't good enough for
something moving money.

Stack: Python, FastAPI, React, TypeScript, WebSockets, Starknet/EVM wallet integration.

#crypto #fintech #python #react #softwareengineering #web3 #tradingsystems

---

## Version B — generic, doesn't name the exchange

🚀 Built a full-stack crypto perpetuals trading terminal from scratch — wallet to UI.

**Meridian** is a self-custodial trading terminal I built end-to-end against a live crypto
derivatives exchange's testnet: Python + FastAPI backend, React/TypeScript dark-themed
frontend, live WebSocket market data, and a complete order lifecycle — place, fill, open
position, live P&L, close, trade history.

A few things that made this more than a weekend CRUD app:

🔧 Diagnosed and routed around **two live bugs in the exchange's own testnet
infrastructure**, found via direct blockchain RPC queries rather than guesswork — and
shipped working workarounds for both without waiting on an upstream fix.

🔐 Implemented the real self-custodial flow: generated a fresh wallet, funded it on a
public testnet, authenticated via Sign-In with Ethereum, and registered a scoped trading
subkey — the same security model real self-custodial platforms use, not a simplified mock.

📊 Full observability: every API call logged, every trade lifecycle run produces a
timestamped evidence report — because "it works on my machine" isn't good enough for
something moving money.

Stack: Python, FastAPI, React, TypeScript, WebSockets, EVM/Starknet wallet integration.

#crypto #fintech #python #react #softwareengineering #web3 #tradingsystems

---

**Notes before you post:**
- Swap in a screenshot from `docs/screenshots/dashboard-overview.png` — posts with an
  image get meaningfully more reach than text-only.
- If you link to a repo, double-check `.env` never got committed (it's gitignored, but
  worth a final look at what's actually pushed).
- "Not financial advice / testnet only" is already in the app footer — worth a one-line
  disclaimer in the post too if you want to be extra safe, e.g. "testnet project, no real
  funds involved."
