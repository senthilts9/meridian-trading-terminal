import type { Bbo, MarketSummary } from "../types";

interface Props {
  markets: string[];
  selected: string;
  onSelect: (market: string) => void;
  summary?: MarketSummary;
  bbo?: Bbo;
}

export function MarketPanel({ markets, selected, onSelect, summary, bbo }: Props) {
  const changePct = summary ? parseFloat(summary.price_change_rate_24h) * 100 : 0;
  const isUp = changePct >= 0;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Market</h2>
        <div className="market-select">
          {markets.map((m) => (
            <button key={m} className={m === selected ? "active" : ""} onClick={() => onSelect(m)}>
              {m.replace("-USD-PERP", "")}
            </button>
          ))}
        </div>
      </div>
      <div className="panel-body">
        <div className="ticker">
          <div className={`price ${isUp ? "up" : "down"}`}>
            {summary ? Number(summary.mark_price).toLocaleString(undefined, { maximumFractionDigits: 2 }) : "--"}
          </div>
          <div className="stat">
            <span className="label">24h Change</span>
            <span className={`value ${isUp ? "up" : "down"}`}>
              {summary ? `${isUp ? "+" : ""}${changePct.toFixed(2)}%` : "--"}
            </span>
          </div>
          <div className="stat">
            <span className="label">24h Volume</span>
            <span className="value">{summary ? Number(summary.volume_24h).toLocaleString() : "--"}</span>
          </div>
          <div className="stat">
            <span className="label">Funding Rate</span>
            <span className="value">{summary ? `${(Number(summary.funding_rate) * 100).toFixed(4)}%` : "--"}</span>
          </div>
        </div>

        <div className="book">
          <div className="side asks">
            <div className="row">
              <span>Ask</span>
              <span>Size</span>
            </div>
            <div className="row">
              <span>{bbo?.ask ?? "--"}</span>
              <span>{bbo?.ask_size ?? "--"}</span>
            </div>
          </div>
          <div className="side bids">
            <div className="row">
              <span>Bid</span>
              <span>Size</span>
            </div>
            <div className="row">
              <span>{bbo?.bid ?? "--"}</span>
              <span>{bbo?.bid_size ?? "--"}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
