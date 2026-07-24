import { useState } from "react";
import { api } from "../api";
import type { Position } from "../types";

export function PositionsTable({ positions, onChanged }: { positions: Position[]; onChanged: () => void }) {
  const [closing, setClosing] = useState<string | null>(null);
  const open = positions.filter((p) => Number(p.size) !== 0);

  async function close(market: string) {
    setClosing(market);
    try {
      await api.closePosition(market);
      onChanged();
    } finally {
      setClosing(null);
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Open Positions</h2>
      </div>
      <table>
        <thead>
          <tr>
            <th>Market</th>
            <th>Side</th>
            <th>Size</th>
            <th>Entry</th>
            <th>Unrealized P&L</th>
            <th>Leverage</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {open.length === 0 && (
            <tr className="empty-row">
              <td colSpan={7}>No open positions</td>
            </tr>
          )}
          {open.map((p) => (
            <tr key={p.market}>
              <td>{p.market}</td>
              <td>
                <span className={`side-badge ${p.side.toLowerCase()}`}>{p.side}</span>
              </td>
              <td>{p.size}</td>
              <td>{p.average_entry_price}</td>
              <td className={Number(p.unrealized_pnl) >= 0 ? "up" : "down"}>{p.unrealized_pnl}</td>
              <td>{p.leverage}x</td>
              <td>
                <button className="close-btn" onClick={() => close(p.market)} disabled={closing === p.market}>
                  {closing === p.market ? "Closing..." : "Close"}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
