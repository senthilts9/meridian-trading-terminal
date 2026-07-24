"""Step: Check fills (executions) resulting from submitted orders."""
from config import DEFAULT_MARKET, get_authenticated_client, logger


def check_fills(p, market: str = DEFAULT_MARKET, page_size: int = 10):
    fills = p.api_client.fetch_fills(params={"market": market, "page_size": page_size})
    logger.info(f"Fills for {market}: {fills}")
    return fills


if __name__ == "__main__":
    p = get_authenticated_client()
    check_fills(p)
