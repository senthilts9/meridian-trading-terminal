"""Step: Close an open position with an opposite reduce_only MARKET order."""
import sys
from decimal import Decimal

from config import DEFAULT_MARKET, get_authenticated_client, logger
from paradex_py.common.order import OrderSide

sys.path.insert(0, ".")
from importlib import import_module  # noqa: E402

place_order_mod = import_module("03_place_order")
position_mod = import_module("06_position_pnl")


def close_position(p, market: str = DEFAULT_MARKET):
    position = position_mod.get_position(p, market)
    if position is None:
        logger.info("Nothing to close.")
        return None

    size = abs(Decimal(position["size"]))
    side_str = position.get("side", "LONG")
    closing_side = OrderSide.Sell if side_str == "LONG" else OrderSide.Buy

    logger.info(f"Closing {side_str} {size} {market} with a reduce_only {closing_side.value}")
    response = place_order_mod.place_market_order(p, market, closing_side, size, reduce_only=True)
    return response


if __name__ == "__main__":
    p = get_authenticated_client()
    close_position(p)
