"""FastAPI backend for the Meridian trading terminal.

Thin wrapper around the same exchange client used by scripts/ -- the
browser never talks to the exchange directly and never sees a private key;
it only ever talks to this server.
"""
import asyncio
import json
import time
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from paradex_py.common.order import Order, OrderSide, OrderType
from schemas import ClosePositionRequest, PlaceOrderRequest

from paradex_client import DEFAULT_MARKET, compute_min_order_size, logger, public_client, trading_client

app = FastAPI(title="Meridian Trading API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

WATCHLIST = ["BTC-USD-PERP", "ETH-USD-PERP"]  # confirmed live on testnet; SOL-USD-PERP isn't listed there


@app.get("/api/health")
def health():
    state = public_client().api_client.fetch_system_state()
    return {"api": "ok", "exchange_testnet": state}


@app.get("/api/markets")
def list_markets():
    """Static config for the watchlist -- tick size, min notional, max leverage, etc."""
    results = []
    for market in WATCHLIST:
        cfg = public_client().api_client.fetch_markets({"market": market})
        if cfg.get("results"):
            results.append(cfg["results"][0])
    return {"results": results}


@app.get("/api/markets/{market}/summary")
def market_summary(market: str):
    return public_client().api_client.fetch_markets_summary({"market": market})


@app.get("/api/markets/{market}/orderbook")
def orderbook(market: str, depth: int = 10):
    return public_client().api_client.fetch_orderbook(market=market, params={"depth": depth})


@app.get("/api/markets/{market}/klines")
def klines(market: str, resolution: str = "15", hours: int = 24):
    end_at = int(time.time() * 1000)
    start_at = end_at - hours * 3600 * 1000
    return public_client().api_client.fetch_klines(
        symbol=market, resolution=resolution, start_at=start_at, end_at=end_at
    )


@app.get("/api/markets/{market}/bbo")
def bbo(market: str):
    return public_client().api_client.fetch_bbo(market=market)


@app.get("/api/account")
def account():
    summary = trading_client().api_client.fetch_account_summary()
    return summary.__dict__ if hasattr(summary, "__dict__") else summary


@app.get("/api/positions")
def positions():
    return trading_client().api_client.fetch_positions()


@app.get("/api/orders")
def open_orders(market: str | None = None):
    params = {"market": market} if market else {}
    return trading_client().api_client.fetch_orders(params=params)


@app.get("/api/orders/history")
def orders_history(market: str | None = None, page_size: int = 20):
    params = {"page_size": page_size}
    if market:
        params["market"] = market
    return trading_client().api_client.fetch_orders_history(params=params)


@app.get("/api/fills")
def fills(market: str | None = None, page_size: int = 20):
    params = {"page_size": page_size}
    if market:
        params["market"] = market
    return trading_client().api_client.fetch_fills(params=params)


@app.post("/api/orders")
def place_order(req: PlaceOrderRequest):
    p = trading_client()
    side = OrderSide.Buy if req.side == "BUY" else OrderSide.Sell

    if req.size:
        size = Decimal(req.size)
    else:
        summary = p.api_client.fetch_markets_summary({"market": req.market})["results"][0]
        market_cfg = p.api_client.fetch_markets({"market": req.market})["results"][0]
        size = compute_min_order_size(market_cfg, float(summary["mark_price"]))

    order_type = OrderType.Market if req.order_type == "MARKET" else OrderType.Limit
    client_id = f"ui_{req.side.lower()}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    order = Order(
        market=req.market,
        order_type=order_type,
        order_side=side,
        size=size,
        limit_price=Decimal(req.limit_price) if req.limit_price else Decimal(0),
        client_id=client_id,
        instruction=req.instruction,
        reduce_only=req.reduce_only,
    )
    response = p.api_client.submit_order(order=order)
    logger.info(f"UI order submitted: {response}")
    return response


@app.post("/api/positions/close")
def close_position(req: ClosePositionRequest):
    p = trading_client()
    positions_resp = p.api_client.fetch_positions()
    position = next(
        (pos for pos in positions_resp.get("results", []) if pos.get("market") == req.market and float(pos.get("size", 0)) != 0),
        None,
    )
    if position is None:
        return {"closed": False, "reason": "no open position"}

    size = abs(Decimal(position["size"]))
    side = OrderSide.Sell if position.get("side") == "LONG" else OrderSide.Buy
    client_id = f"ui_close_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    order = Order(
        market=req.market,
        order_type=OrderType.Market,
        order_side=side,
        size=size,
        client_id=client_id,
        instruction="IOC",
        reduce_only=True,
    )
    response = p.api_client.submit_order(order=order)
    logger.info(f"UI close-position order submitted: {response}")
    return response


@app.websocket("/ws/{market}")
async def ws_market_feed(websocket: WebSocket, market: str):
    """Lightweight polling relay: pushes BBO + account + positions on an
    interval so the UI updates live without the browser polling REST itself.
    (Paradex's own WS channel protocol is a further upgrade -- this is the
    pragmatic v1: correct data, simple implementation.)"""
    await websocket.accept()
    try:
        while True:
            payload = {
                "type": "tick",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "bbo": public_client().api_client.fetch_bbo(market=market),
                "account": trading_client().api_client.fetch_account_summary().__dict__,
                "positions": trading_client().api_client.fetch_positions(),
            }
            await websocket.send_text(json.dumps(payload, default=str))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        logger.info(f"WS client disconnected from {market} feed")
