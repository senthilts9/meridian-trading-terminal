export interface MarketConfig {
  symbol: string;
  base_currency: string;
  quote_currency: string;
  order_size_increment: string;
  price_tick_size: string;
  min_notional: string;
  max_order_size: string;
}

export interface MarketSummary {
  symbol: string;
  mark_price: string;
  last_traded_price: string;
  bid: string;
  bid_size: string;
  ask: string;
  ask_size: string;
  volume_24h: string;
  funding_rate: string;
  price_change_rate_24h: string;
}

export interface Bbo {
  market: string;
  bid: string;
  bid_size: string;
  ask: string;
  ask_size: string;
  last_updated_at: number;
}

export interface AccountSummary {
  account: string;
  account_value: string;
  free_collateral: string;
  initial_margin_requirement: string;
  maintenance_margin_requirement: string;
  status: string;
}

export interface Position {
  market: string;
  status: string;
  side: "LONG" | "SHORT";
  size: string;
  average_entry_price: string;
  unrealized_pnl: string;
  leverage: string;
  liquidation_price: string;
}

export interface OrderRecord {
  id: string;
  market: string;
  side: "BUY" | "SELL";
  type: string;
  size: string;
  remaining_size: string;
  status: string;
  avg_fill_price: string;
  client_id: string;
  created_at: number;
}

export interface Candle {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface Fill {
  id: string;
  side: "BUY" | "SELL";
  market: string;
  price: string;
  size: string;
  fee: string;
  realized_pnl: string;
  created_at: number;
}
