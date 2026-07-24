# Demo Command Reference — copy/paste ready

**Author:** Senthil Saravanamuthu

Every command below runs against our own backend (`127.0.0.1:8000`), which holds the
exchange session internally — you never need to attach a token yourself for these. Backend
must be running: `cd backend && uvicorn main:app --reload --port 8000`.

## 1. Health check
```bash
curl -s http://127.0.0.1:8000/api/health
```

## 2. Market spec (all watchlist markets)
```bash
curl -s http://127.0.0.1:8000/api/markets
```

## 3. Live price/stats
```bash
curl -s "http://127.0.0.1:8000/api/markets/BTC-USD-PERP/summary"
```

## 4. Order book
```bash
curl -s "http://127.0.0.1:8000/api/markets/BTC-USD-PERP/orderbook?depth=5"
```

## 5. Best bid/ask
```bash
curl -s "http://127.0.0.1:8000/api/markets/BTC-USD-PERP/bbo"
```

## 6. Candles (15min resolution, last 24h)
```bash
curl -s "http://127.0.0.1:8000/api/markets/BTC-USD-PERP/klines?resolution=15&hours=24"
```

## 9. Account snapshot
```bash
curl -s http://127.0.0.1:8000/api/account
```

## 11. Positions
```bash
curl -s http://127.0.0.1:8000/api/positions
```

## 14. Place order (BUY, auto-sized)
```bash
curl -s -X POST http://127.0.0.1:8000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"market":"BTC-USD-PERP","side":"BUY","instruction":"IOC"}'
```

## 15. Check open orders / order history
```bash
curl -s "http://127.0.0.1:8000/api/orders?market=BTC-USD-PERP"
curl -s "http://127.0.0.1:8000/api/orders/history?market=BTC-USD-PERP"
```

## 16. Check fills
```bash
curl -s "http://127.0.0.1:8000/api/fills?market=BTC-USD-PERP"
```

## 17. Close position
```bash
curl -s -X POST http://127.0.0.1:8000/api/positions/close \
  -H "Content-Type: application/json" \
  -d '{"market":"BTC-USD-PERP"}'
```

## 18. Trade history
```bash
curl -s "http://127.0.0.1:8000/api/fills?market=BTC-USD-PERP&page_size=20"
```

## C++ risk model (no URL, no key — local execution only)
```bash
cd ~/paradex-trading-bot/quant-cpp
g++ -std=c++17 -O2 -static -o cmle.exe main.cpp liquidation_model.cpp   # rebuild fresh -- see note below
./cmle.exe --side SHORT --entry 66000 --size 0.00023 \
  --collateral 100001.00961987 --imf-base 0.02 --mmf-factor 0.5 \
  --actual 430351430.25096846
```

**Note:** rebuild (`g++ ...`) immediately before running each time during a live demo —
the compiled `.exe` has been observed getting silently removed after a delay (likely
Windows Defender / corporate antivirus quarantining an unsigned freshly-built binary).
Building and running back-to-back avoids the gap.

## Proving the C++ output isn't hardcoded
Run it twice with different inputs and show the output changes accordingly:
```bash
./cmle.exe --side SHORT --entry 66000 --size 0.00023 --collateral 100001.00961987 --imf-base 0.02 --mmf-factor 0.5
./cmle.exe --side SHORT --entry 66000 --size 0.00046 --collateral 100001.00961987 --imf-base 0.02 --mmf-factor 0.5
```
Doubling size should roughly halve the estimate (size is in the denominator) — real
computation, not a fixed string.
