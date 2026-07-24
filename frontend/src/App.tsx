import { useCallback, useEffect, useRef, useState } from "react";
import { api, WS_BASE_URL } from "./api";
import { AccountPanel } from "./components/AccountPanel";
import { FillsTable } from "./components/FillsTable";
import { Footer } from "./components/Footer";
import { Header } from "./components/Header";
import { MarketPanel } from "./components/MarketPanel";
import { OrderTicket } from "./components/OrderTicket";
import { OrdersTable } from "./components/OrdersTable";
import { PositionsTable } from "./components/PositionsTable";
import { PriceChart } from "./components/PriceChart";
import type { AccountSummary, Bbo, Candle, Fill, MarketSummary, OrderRecord, Position } from "./types";

const MARKETS = ["BTC-USD-PERP", "ETH-USD-PERP"];

export default function App() {
  const [apiOk, setApiOk] = useState<boolean | null>(null);
  const [market, setMarket] = useState(MARKETS[0]);
  const [summary, setSummary] = useState<MarketSummary>();
  const [bbo, setBbo] = useState<Bbo>();
  const [account, setAccount] = useState<AccountSummary>();
  const [positions, setPositions] = useState<Position[]>([]);
  const [openOrders, setOpenOrders] = useState<OrderRecord[]>([]);
  const [history, setHistory] = useState<OrderRecord[]>([]);
  const [fills, setFills] = useState<Fill[]>([]);
  const [candles, setCandles] = useState<Candle[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const refreshSnapshot = useCallback(async () => {
    const [openOrdersRes, historyRes, fillsRes, summaryRes] = await Promise.all([
      api.openOrders(market),
      api.ordersHistory(market),
      api.fills(market),
      api.marketSummary(market),
    ]);
    setOpenOrders((openOrdersRes as { results: OrderRecord[] }).results);
    setHistory((historyRes as { results: OrderRecord[] }).results);
    setFills((fillsRes as { results: Fill[] }).results);
    setSummary((summaryRes as { results: MarketSummary[] }).results[0]);
  }, [market]);

  // Health check
  useEffect(() => {
    api
      .health()
      .then(() => setApiOk(true))
      .catch(() => setApiOk(false));
  }, []);

  // Snapshot refresh on market change / after actions
  useEffect(() => {
    refreshSnapshot().catch(console.error);
  }, [refreshSnapshot]);

  // Candles: fetch on market change, then refresh every 30s
  useEffect(() => {
    let cancelled = false;
    const load = () => {
      api
        .klines(market, "15", 24)
        .then((res) => {
          if (cancelled) return;
          const parsed = res.results.map(([time, open, high, low, close, volume]) => ({
            time,
            open,
            high,
            low,
            close,
            volume,
          }));
          setCandles(parsed);
        })
        .catch(console.error);
    };
    load();
    const interval = setInterval(load, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [market]);

  // Live feed: BBO + account + positions over WebSocket
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/${market}`);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setBbo(data.bbo);
      setAccount(data.account);
      setPositions((data.positions?.results as Position[]) ?? []);
    };
    ws.onerror = () => setApiOk(false);
    return () => ws.close();
  }, [market]);

  return (
    <div className="app">
      <Header apiOk={apiOk} accountAddress={account?.account} />
      <div className="layout">
        <div className="col">
          <MarketPanel markets={MARKETS} selected={market} onSelect={setMarket} summary={summary} bbo={bbo} />
          <PriceChart candles={candles} market={market} />
          <PositionsTable positions={positions} onChanged={refreshSnapshot} />
          <OrdersTable orders={openOrders} title="Open Orders" />
          <OrdersTable orders={history} title="Order History" />
          <FillsTable fills={fills} />
        </div>
        <div className="col">
          <AccountPanel account={account} />
          <OrderTicket market={market} onOrderSubmitted={refreshSnapshot} />
        </div>
      </div>
      <Footer />
    </div>
  );
}
