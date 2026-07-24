"""Step: Get market data. Public endpoints, no auth/wallet required."""
from config import get_public_client, logger

MARKET = "BTC-USD-PERP"


def main():
    p = get_public_client()

    markets = p.api_client.fetch_markets({"market": MARKET})
    logger.info(f"Market config for {MARKET}: {markets}")

    summary = p.api_client.fetch_markets_summary({"market": MARKET})
    logger.info(f"24h summary: {summary}")

    orderbook = p.api_client.fetch_orderbook(market=MARKET, params={"depth": 5})
    logger.info(f"Orderbook (depth 5): {orderbook}")

    bbo = p.api_client.fetch_bbo(market=MARKET)
    logger.info(f"BBO: {bbo}")

    return {"markets": markets, "summary": summary, "orderbook": orderbook, "bbo": bbo}


if __name__ == "__main__":
    main()
