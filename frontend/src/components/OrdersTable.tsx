import type { OrderRecord } from "../types";

export function OrdersTable({ orders, title }: { orders: OrderRecord[]; title: string }) {
  return (
    <div className="panel">
      <div className="panel-header">
        <h2>{title}</h2>
      </div>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Market</th>
            <th>Side</th>
            <th>Type</th>
            <th>Size</th>
            <th>Avg Fill</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {orders.length === 0 && (
            <tr className="empty-row">
              <td colSpan={7}>No orders yet</td>
            </tr>
          )}
          {orders.map((o) => (
            <tr key={o.id}>
              <td>{new Date(o.created_at).toLocaleTimeString()}</td>
              <td>{o.market}</td>
              <td>
                <span className={`side-badge ${o.side.toLowerCase()}`}>{o.side}</span>
              </td>
              <td>{o.type}</td>
              <td>{o.size}</td>
              <td>{o.avg_fill_price || "--"}</td>
              <td>{o.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
