import { useMemo, useState } from "react";
import type { Candle } from "../types";

interface Props {
  candles: Candle[];
  market: string;
}

const WIDTH = 760;
const HEIGHT = 220;
const PAD_LEFT = 56;
const PAD_RIGHT = 12;
const PAD_TOP = 12;
const PAD_BOTTOM = 24;

export function PriceChart({ candles, market }: Props) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);

  const plot = useMemo(() => {
    if (candles.length === 0) return null;

    const highs = candles.map((c) => c.high);
    const lows = candles.map((c) => c.low);
    let maxP = Math.max(...highs);
    let minP = Math.min(...lows);
    if (maxP === minP) {
      // flat series (common on a quiet testnet market) -- fake a small band so it still renders
      maxP += 1;
      minP -= 1;
    }
    const padP = (maxP - minP) * 0.08;
    maxP += padP;
    minP -= padP;

    const innerW = WIDTH - PAD_LEFT - PAD_RIGHT;
    const innerH = HEIGHT - PAD_TOP - PAD_BOTTOM;
    const slot = innerW / candles.length;
    const bodyW = Math.max(2, Math.min(14, slot - 2)); // 2px surface gap between candles

    const y = (price: number) => PAD_TOP + innerH * (1 - (price - minP) / (maxP - minP));
    const x = (i: number) => PAD_LEFT + slot * i + slot / 2;

    const priceTicks = 4;
    const gridLines = Array.from({ length: priceTicks + 1 }, (_, i) => {
      const price = minP + ((maxP - minP) * i) / priceTicks;
      return { price, y: y(price) };
    });

    return { minP, maxP, x, y, bodyW, slot, gridLines, innerW, innerH };
  }, [candles]);

  if (!plot || candles.length === 0) {
    return (
      <div className="panel">
        <div className="panel-header">
          <h2>Price Chart</h2>
        </div>
        <div className="panel-body">
          <p style={{ color: "var(--dim)", fontSize: 12.5 }}>No candle data yet.</p>
        </div>
      </div>
    );
  }

  const hovered = hoverIdx !== null ? candles[hoverIdx] : null;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Price Chart · {market.replace("-USD-PERP", "")} · 15m</h2>
      </div>
      <div className="panel-body">
        <svg
          viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
          width="100%"
          height={HEIGHT}
          onMouseLeave={() => setHoverIdx(null)}
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const relX = ((e.clientX - rect.left) / rect.width) * WIDTH;
            const idx = Math.min(candles.length - 1, Math.max(0, Math.floor((relX - PAD_LEFT) / plot.slot)));
            setHoverIdx(idx);
          }}
        >
          {/* Recessive gridlines + price labels */}
          {plot.gridLines.map((g, i) => (
            <g key={i}>
              <line
                x1={PAD_LEFT}
                x2={WIDTH - PAD_RIGHT}
                y1={g.y}
                y2={g.y}
                stroke="var(--border)"
                strokeWidth={1}
              />
              <text x={4} y={g.y + 3} fontSize={9.5} fill="var(--muted)" fontFamily="var(--mono)">
                {g.price.toLocaleString(undefined, { maximumFractionDigits: 1 })}
              </text>
            </g>
          ))}

          {/* Candles */}
          {candles.map((c, i) => {
            const isUp = c.close >= c.open;
            const color = isUp ? "var(--green)" : "var(--red)";
            const cx = plot.x(i);
            const bodyTop = plot.y(Math.max(c.open, c.close));
            const bodyBottom = plot.y(Math.min(c.open, c.close));
            const bodyHeight = Math.max(1.5, bodyBottom - bodyTop);
            return (
              <g key={c.time}>
                <line x1={cx} x2={cx} y1={plot.y(c.high)} y2={plot.y(c.low)} stroke={color} strokeWidth={1.5} />
                <rect
                  x={cx - plot.bodyW / 2}
                  y={bodyTop}
                  width={plot.bodyW}
                  height={bodyHeight}
                  rx={1.5}
                  fill={color}
                />
              </g>
            );
          })}

          {/* Hover crosshair */}
          {hoverIdx !== null && (
            <line
              x1={plot.x(hoverIdx)}
              x2={plot.x(hoverIdx)}
              y1={PAD_TOP}
              y2={HEIGHT - PAD_BOTTOM}
              stroke="var(--muted)"
              strokeWidth={1}
              strokeDasharray="3,3"
            />
          )}
        </svg>

        {hovered ? (
          <div className="stat-grid" style={{ marginTop: 8 }}>
            <div className="stat-tile">
              <div className="label">Time</div>
              <div className="value">{new Date(hovered.time).toLocaleTimeString()}</div>
            </div>
            <div className="stat-tile">
              <div className="label">Open / Close</div>
              <div className="value">
                {hovered.open.toLocaleString()} / {hovered.close.toLocaleString()}
              </div>
            </div>
            <div className="stat-tile">
              <div className="label">High</div>
              <div className="value up">{hovered.high.toLocaleString()}</div>
            </div>
            <div className="stat-tile">
              <div className="label">Low</div>
              <div className="value down">{hovered.low.toLocaleString()}</div>
            </div>
          </div>
        ) : (
          <p style={{ color: "var(--dim)", fontSize: 11, marginTop: 8 }}>Hover the chart for OHLC detail.</p>
        )}
      </div>
    </div>
  );
}
