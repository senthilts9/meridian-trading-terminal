interface Props {
  apiOk: boolean | null;
  accountAddress?: string;
}

export function Header({ apiOk, accountAddress }: Props) {
  return (
    <header className="header">
      <div className="brand">
        <h1>Meridian</h1>
        <span className="env-pill">TESTNET</span>
      </div>
      <div className="status">
        {accountAddress && (
          <span>
            {accountAddress.slice(0, 6)}...{accountAddress.slice(-4)}
          </span>
        )}
        <span className={`dot ${apiOk === null ? "" : apiOk ? "ok" : "err"}`} />
        <span>{apiOk === null ? "connecting" : apiOk ? "API live" : "API down"}</span>
      </div>
    </header>
  );
}
