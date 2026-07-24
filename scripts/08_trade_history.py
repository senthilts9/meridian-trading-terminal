"""Step: Trade history — closed orders, fills, and account transactions."""
from config import DEFAULT_MARKET, get_authenticated_client, logger


def trade_history(p, market: str = DEFAULT_MARKET, page_size: int = 20):
    orders_history = p.api_client.fetch_orders_history(params={"market": market, "page_size": page_size})
    logger.info(f"Orders history: {orders_history}")

    fills = p.api_client.fetch_fills(params={"market": market, "page_size": page_size})
    logger.info(f"Fills: {fills}")

    transactions = p.api_client.fetch_transactions(params={"page_size": page_size})
    logger.info(f"Account transactions: {transactions}")

    return {"orders_history": orders_history, "fills": fills, "transactions": transactions}


if __name__ == "__main__":
    p = get_authenticated_client()
    trade_history(p)
