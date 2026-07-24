"""Step: Monitor open position(s) and unrealized P&L."""
from config import DEFAULT_MARKET, get_authenticated_client, logger


def get_position(p, market: str = DEFAULT_MARKET):
    positions = p.api_client.fetch_positions()
    logger.info(f"All positions: {positions}")
    for pos in positions.get("results", []):
        if pos.get("market") == market and float(pos.get("size", 0)) != 0:
            logger.info(f"Open position on {market}: {pos}")
            return pos
    logger.info(f"No open position on {market}")
    return None


def get_account_pnl(p):
    summary = p.api_client.fetch_account_summary()
    logger.info(f"Account summary (value/margin/PnL): {summary}")
    return summary


if __name__ == "__main__":
    p = get_authenticated_client()
    get_position(p)
    get_account_pnl(p)
