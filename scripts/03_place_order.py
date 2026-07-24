"""Step: Place a BUY order. Opens (or adds to) a position on fill."""
import sys
from datetime import datetime
from decimal import Decimal

from config import DEFAULT_MARKET, compute_min_order_size, get_authenticated_client, logger
from paradex_py.common.order import Order, OrderSide, OrderType


def place_market_order(p, market: str, side: OrderSide, size: Decimal, reduce_only: bool = False):
    client_id = f"bot_{side.value.lower()}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    order = Order(
        market=market,
        order_type=OrderType.Market,
        order_side=side,
        size=size,
        client_id=client_id,
        instruction="IOC",  # immediate-or-cancel: fill now at best price, or cancel
        reduce_only=reduce_only,
    )
    response = p.api_client.submit_order(order=order)
    logger.info(f"Submitted {side.value} order: {response}")
    return response


def main():
    p = get_authenticated_client()

    summary = p.api_client.fetch_markets_summary({"market": DEFAULT_MARKET})["results"][0]
    mark_price = float(summary["mark_price"])
    market_cfg = p.api_client.fetch_markets({"market": DEFAULT_MARKET})["results"][0]

    size = compute_min_order_size(market_cfg, mark_price)
    logger.info(f"{DEFAULT_MARKET} mark_price={mark_price} -> order size={size}")

    response = place_market_order(p, DEFAULT_MARKET, OrderSide.Buy, size)
    if not response.get("id"):
        logger.error(f"Order submission failed: {response}")
        sys.exit(1)
    return response


if __name__ == "__main__":
    main()
