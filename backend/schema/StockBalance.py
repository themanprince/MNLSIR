from pydantic import BaseModel
from typing import List


class StockBalanceItem(BaseModel):
    product_id: int
    product_name: str
    quantity: float
    unit_symbol: str

    model_config = {
        "from_attributes": True
    }


class StockBalanceOut(BaseModel):
    items: List[StockBalanceItem]