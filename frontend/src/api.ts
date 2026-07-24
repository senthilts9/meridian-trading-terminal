const BASE_URL = "http://127.0.0.1:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json();
}

export const api = {
  health: () => request("/api/health"),
  markets: () => request<{ results: unknown[] }>("/api/markets"),
  marketSummary: (market: string) => request(`/api/markets/${market}/summary`),
  orderbook: (market: string, depth = 10) => request(`/api/markets/${market}/orderbook?depth=${depth}`),
  bbo: (market: string) => request(`/api/markets/${market}/bbo`),
  klines: (market: string, resolution = "15", hours = 24) =>
    request<{ results: number[][] }>(`/api/markets/${market}/klines?resolution=${resolution}&hours=${hours}`),
  account: () => request("/api/account"),
  positions: () => request<{ results: unknown[] }>("/api/positions"),
  openOrders: (market?: string) => request<{ results: unknown[] }>(`/api/orders${market ? `?market=${market}` : ""}`),
  ordersHistory: (market?: string) =>
    request<{ results: unknown[] }>(`/api/orders/history${market ? `?market=${market}` : ""}`),
  fills: (market?: string) => request<{ results: unknown[] }>(`/api/fills${market ? `?market=${market}` : ""}`),
  placeOrder: (body: {
    market: string;
    side: "BUY" | "SELL";
    size?: string;
    order_type?: "MARKET" | "LIMIT";
    limit_price?: string;
    instruction?: "GTC" | "IOC" | "POST_ONLY";
    reduce_only?: boolean;
  }) => request("/api/orders", { method: "POST", body: JSON.stringify(body) }),
  closePosition: (market: string) =>
    request("/api/positions/close", { method: "POST", body: JSON.stringify({ market }) }),
};

export const WS_BASE_URL = "ws://127.0.0.1:8000";
