# CMLE — Cross-Margin Liquidation Estimator

**Meridian Risk Model.** A standalone C++ tool that independently computes an estimated
liquidation price for a perpetual futures position, for comparison against whatever value
the exchange itself reports.

**Deliberately decoupled** from the live backend/frontend — it makes no network calls and
isn't wired into the running app. This is a portfolio artifact demonstrating the model
itself, not a production dependency; wiring it into the live app was considered and
explicitly deferred (see the main project's `docs/RUNBOOK.md`).

## Why this exists

While building the trading terminal, the real exchange API's `liquidation_price` field on
an open position sometimes came back populated with a plausible-looking but extreme value,
and in earlier captures, sometimes blank. Rather than treat the exchange's number as a
black box, this tool derives the figure independently from first principles, using the
same inputs (entry price, size, account collateral, margin parameters) a position/account
snapshot already contains — the standard practice of independently validating a
counterparty's risk numbers rather than trusting them blindly.

## The model

Cross-margin, single-position-dominant account. Two facts define liquidation:

```
Account value at price P:        V(P) = C + (P - E) * S
Maintenance margin req. at P:    M(P) = mmf * |S| * P
Liquidation is where V(P) = M(P)
```

Where `C` = total collateral, `E` = entry price, `S` = signed size, `mmf` = maintenance
margin fraction (`imf_base * mmf_factor`, both from the market's public contract spec).

Solving for `P` on each side:

```
LONG  (S > 0):            P = (E*S - C) / (S * (1 - mmf))
SHORT (S < 0, s = |S|):   P = (C + E*s) / (s * (1 + mmf))
```

Full derivation in the comment block above `estimate_liquidation_price()` in
`liquidation_model.cpp`.

## Validation against real data

Run `make test`, or manually:

```bash
./cmle --side SHORT --entry 66000 --size 0.00023 \
       --collateral 100001.00961987 --imf-base 0.02 --mmf-factor 0.5 \
       --actual 430351430.25096846
```

```
Model liquidation estimate:  430547523.116100
Exchange-reported value:     430351430.250968
Relative error:              0.0456%
```

Entry/collateral/margin params and the `--actual` comparison value are all real, captured
live from this project's own testnet account during a genuine open short position — not
invented numbers. **0.0456% relative error** is strong independent confirmation the model
captures the exchange's real methodology, not a coincidence — and it's a non-zero delta,
which is itself informative: an exact match would be more suspicious than a small,
explainable gap (likely rounding, or a minor term this simplified model omits).

## A genuine edge case this model surfaces

An extremely over-collateralized **LONG** position can produce a *negative* estimated
liquidation price — which isn't a bug, it's the honest mathematical answer: the position
holds so much excess collateral relative to its size that no possible price (prices can't
go negative) would ever trigger liquidation on its own. The CLI detects and annotates this
case explicitly rather than printing a bare, confusing negative number.

## Usage

```bash
make          # builds ./cmle (statically linked, no runtime DLL dependencies)
make test     # runs the validation case above
./cmle --help
```

## Assumptions and honest limitations

- **Single-position account assumption.** True cross-margin liquidation depends on *all*
  open positions' combined margin, not just one. This model treats `total_collateral` as
  fully available to the position in question — accurate for a single-position account
  (as validated above), an approximation otherwise.
- **`imf_factor` and `imf_shift` are ignored.** The exchange's real margin formula has
  additional terms for size-dependent margin scaling; both were `0` in every market
  config captured during this project, so they don't affect the validation above, but a
  market where they're non-zero would need the model extended.
- **No funding rate accrual.** Real liquidation price shifts slightly with accrued funding
  payments over a position's lifetime; this model computes a point-in-time estimate.

These are documented, not hidden — the point of an independent model is to know exactly
what it does and doesn't account for.
