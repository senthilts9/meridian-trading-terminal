# Anticipated Follow-Up Questions

**Author:** Senthil Saravanamuthu

Likely questions a technically sharp interviewer asks after seeing the L1/L2 wallet demo
and the trading lifecycle, with concise answers.

---

### "Why separate the L1 key, the L2 account, and the subkey — why not just one key?"

Security isolation. The L1 key is the root of trust — if it's ever compromised, the
attacker owns everything. The subkey can only sign orders (`can_withdraw: False`) — if
*it* leaks, the attacker can trade with your money but can never move it out. That's a
real, deliberate blast-radius reduction, not incidental complexity.

### "What can someone do if they steal just the subkey?"

Place and cancel orders. Nothing else — no withdrawals, no account changes, no ability to
register new subkeys. Worst case is bad trades, not stolen funds.

### "What if you lose the L1 private key?"

You lose access to that L2 account permanently — there's no password reset, no customer
support recovery. That's the tradeoff of true self-custody: no third party *can*
intervene, which is also why it's more secure than a custodial exchange holding your
private key for you.

### "Is this really self-custodial if the exchange's contracts control settlement?"

Yes, in the meaningful sense: the exchange never has your private key, and the smart contracts
enforce the rules (no arbitrary fund seizure) rather than a company's internal database.
Compare to a CEX: on Binance, the private key belongs to Binance — you're trusting a
company. Here, you sign every order-authorizing action yourself; the exchange can match
your orders but can't move your collateral without a signature only you can produce.

### "How is the L2 account address derived from the L1 key?"

Deterministically, via a SIWE (Sign-In With Ethereum, EIP-4361) signature — the same L1
key always produces the same L2 address. No separate seed phrase to back up; your
Ethereum wallet *is* your exchange identity.

### "Why IOC instead of GTC for most of your demo orders?"

IOC (Immediate-Or-Cancel) guarantees no resting state — it either fills right now or
disappears, which made automated testing deterministic (no orphaned orders to clean up
between test runs). I did demo a GTC/LIMIT order separately specifically to show the
resting-order lifecycle, since IOC alone never populates the "Open Orders" table.

### "What causes an order to get EMPTY_MARKET or TIMEOUT?"

`EMPTY_MARKET` = literally zero resting liquidity on the side you need to match against
at that instant. `TIMEOUT` = similar outcome, different internal trigger (the order waited
past its allowed window without a match). Both are the exchange correctly refusing to let
an IOC order wait — that's the definition of IOC, not a bug.

### "How is liquidation price calculated, and why was it blank sometimes?"

Cross-margin liquidation price accounts for your *entire* account's collateral backing
each position, not just that position's isolated margin — so a small position backed by
large total collateral can show an extreme (or blank, in some states) liquidation price
because it's nowhere near at risk. I don't fully know the exact server-side condition for
when the exchange leaves it blank vs. populated — that's flagged as open follow-up, not glossed
over. [This is also why I proposed, and you chose, a standalone C++ model to independently
compute an estimate for comparison rather than assuming it's always available.]

### "Why FastAPI + React instead of using the exchange's own web app?"

To prove I can build the full stack myself, not just consume someone else's UI — and to
demonstrate the security pattern properly (backend holds keys, browser never does), which
you don't get to control when using a third party's frontend.

### "REST polling vs. WebSocket — which does your app use, and why?"

Currently a polling relay (backend fetches account/positions/BBO every 2s, pushes to the
browser over its own WebSocket) rather than subscribing to the exchange's native WS channels
directly. Deliberate v1 tradeoff: correct data, simple to reason about, shipped fast.
Documented as the clear next upgrade if latency mattered for a real strategy.

### "What would you say isn't production-ready yet?"

Three things, honestly: (1) the WS relay is polling-based, not a true low-latency
subscription; (2) no persistent database — state lives in the exchange's API and our own log
files, not a queryable store; (3) no automated test suite — verification so far has been
live manual/scripted runs against testnet, not CI-gated unit/integration tests.

### "You mentioned finding real bugs in the exchange's testnet — walk me through how."

Two independent issues, both found by not trusting a stack trace at face value: (1) an
account-deploy transaction reverted — instead of guessing, I queried the Starknet RPC
directly for the revert reason, which named an undeclared contract class referenced by
the exchange's own `/system/config`. (2) The SDK's subkey-registration helper failed with a
missing-signature error — I read the actual API error message, found the documented field
requirements, and hand-built the correct payload instead of assuming the SDK must be right.

### "How do you know the numbers in your UI are real and not mocked?"

Every field traces to a specific exchange REST endpoint with zero computation in between —
`backend/main.py` is essentially one-line pass-throughs. The only client-side computation
is default order sizing (before submission) and a percentage-format conversion for display.
Happy to open DevTools live and show the actual network calls.
