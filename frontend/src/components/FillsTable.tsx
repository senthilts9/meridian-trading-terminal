import type { Fill } from "../types";

export function FillsTable({ fills }: { fills: Fill[] }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Fills</h2>
      </div>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Market</th>
            <th>Side</th>
            <th>Price</th>
            <th>Size</th>
            <th>Fee</th>
            <th>Realized P&L</th>
          </tr>
        </thead>
        <tbody>
          {fills.length === 0 && (
            <tr className="empty-row">
              <td colSpan={7}>No fills yet</td>
            </tr>
          )}
          {fills.map((f) => (
            <tr key={f.id}>
              <td>{new Date(f.created_at).toLocaleTimeString()}</td>
              <td>{f.market}</td>
              <td>
                <span className={`side-badge ${f.side.toLowerCase()}`}>{f.side}</span>
              </td>
              <td>{f.price}</td>
              <td>{f.size}</td>
              <td>{f.fee}</td>
              <td className={Number(f.realized_pnl) >= 0 ? "up" : "down"}>{f.realized_pnl}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
