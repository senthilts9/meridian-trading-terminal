import { useState } from "react";
import { api } from "../api";

interface Props {
  market: string;
  onOrderSubmitted: () => void;
}

export function OrderTicket({ market, onOrderSubmitted }: Props) {
  const [side, setSide] = useState<"BUY" | "SELL">("BUY");
  const [orderType, setOrderType] = useState<"MARKET" | "LIMIT">("MARKET");
  const [size, setSize] = useState("");
  const [limitPrice, setLimitPrice] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [toast, setToast] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  async function submit() {
    setSubmitting(true);
    setToast(null);
    try {
      const result = await api.placeOrder({
        market,
        side,
        size: size || undefined,
        order_type: orderType,
        limit_price: orderType === "LIMIT" ? limitPrice : undefined,
        instruction: orderType === "LIMIT" ? "GTC" : "IOC",
      });
      const r = result as { status?: string; avg_fill_price?: string; id?: string };
      setToast({
        kind: "success",
        text: `${side} order ${r.status ?? "submitted"}${r.avg_fill_price ? ` @ ${r.avg_fill_price}` : ""} (id ${r.id?.slice(-6)})`,
      });
      onOrderSubmitted();
    } catch (err) {
      setToast({ kind: "error", text: String(err) });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Order Ticket</h2>
      </div>
      <div className="panel-body">
        <div className="ticket-tabs">
          <button className={`buy ${side === "BUY" ? "active" : ""}`} onClick={() => setSide("BUY")}>
            Buy / Long
          </button>
          <button className={`sell ${side === "SELL" ? "active" : ""}`} onClick={() => setSide("SELL")}>
            Sell / Short
          </button>
        </div>

        <div className="field">
          <label>Market</label>
          <input value={market} disabled />
        </div>

        <div className="field">
          <label>Order Type</label>
          <select value={orderType} onChange={(e) => setOrderType(e.target.value as "MARKET" | "LIMIT")}>
            <option value="MARKET">Market (IOC)</option>
            <option value="LIMIT">Limit (GTC)</option>
          </select>
        </div>

        <div className="field">
          <label>Size (blank = auto minimum)</label>
          <input
            placeholder="0.0002"
            value={size}
            onChange={(e) => setSize(e.target.value)}
            inputMode="decimal"
          />
        </div>

        {orderType === "LIMIT" && (
          <div className="field">
            <label>Limit Price</label>
            <input
              placeholder="66000"
              value={limitPrice}
              onChange={(e) => setLimitPrice(e.target.value)}
              inputMode="decimal"
            />
          </div>
        )}

        <button
          className={`submit-btn ${side === "BUY" ? "buy" : "sell"}`}
          onClick={submit}
          disabled={submitting || (orderType === "LIMIT" && !limitPrice)}
        >
          {submitting ? "Submitting..." : `${side} ${market.replace("-USD-PERP", "")}`}
        </button>

        {toast && <div className={`toast ${toast.kind}`}>{toast.text}</div>}
      </div>
    </div>
  );
}
