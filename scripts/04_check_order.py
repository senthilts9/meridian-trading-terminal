"""Step: Check order status by id or client_id."""
from config import get_authenticated_client, logger


def check_order(p, order_id: str = None, client_id: str = None):
    if order_id:
        order = p.api_client.fetch_order(order_id=order_id)
    elif client_id:
        order = p.api_client.fetch_order_by_client_id(client_id=client_id)
    else:
        raise ValueError("Provide order_id or client_id")
    logger.info(f"Order status: {order}")
    return order


def list_open_orders(p, market: str = None):
    params = {"market": market} if market else {}
    orders = p.api_client.fetch_orders(params=params)
    logger.info(f"Open orders: {orders}")
    return orders


if __name__ == "__main__":
    p = get_authenticated_client()
    list_open_orders(p)
