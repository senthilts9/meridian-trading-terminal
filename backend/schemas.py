from typing import Literal, Optional

from pydantic import BaseModel


class PlaceOrderRequest(BaseModel):
    market: str
    side: Literal["BUY", "SELL"]
    size: Optional[str] = None  # if omitted, backend computes the minimum valid size
    order_type: Literal["MARKET", "LIMIT"] = "MARKET"
    limit_price: Optional[str] = None
    instruction: Literal["GTC", "IOC", "POST_ONLY"] = "IOC"
    reduce_only: bool = False


class ClosePositionRequest(BaseModel):
    market: str
