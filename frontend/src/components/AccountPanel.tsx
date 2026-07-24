import type { AccountSummary } from "../types";

export function AccountPanel({ account }: { account?: AccountSummary }) {
  const fmt = (v?: string) =>
    v ? Number(v).toLocaleString(undefined, { maximumFractionDigits: 2 }) : "--";

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Account</h2>
        {account && (
          <span className={`side-badge ${account.status === "ACTIVE" ? "long" : "short"}`}>{account.status}</span>
        )}
      </div>
      <div className="panel-body">
        <div className="stat-grid">
          <div className="stat-tile">
            <div className="label">Account Value</div>
            <div className="value">${fmt(account?.account_value)}</div>
          </div>
          <div className="stat-tile">
            <div className="label">Free Collateral</div>
            <div className="value">${fmt(account?.free_collateral)}</div>
          </div>
          <div className="stat-tile">
            <div className="label">Initial Margin</div>
            <div className="value">${fmt(account?.initial_margin_requirement)}</div>
          </div>
          <div className="stat-tile">
            <div className="label">Maint. Margin</div>
            <div className="value">${fmt(account?.maintenance_margin_requirement)}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
