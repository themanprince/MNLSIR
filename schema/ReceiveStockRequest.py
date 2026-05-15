from pydantic import BaseModel
from typing import List
from decimal import Decimal
from datetime import date


class ReceiveStockRequest(BaseModel):
    store_id: int
    date: date
    source_party: str
    remarks: str
    items: List[ReceiveIssueItem]


class ReceiveIssueItem(BaseModel):
    product_id: int
    unit_id: int
    quantity: Decimal