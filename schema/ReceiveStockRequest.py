from pydantic import BaseModel
from typing import List
from decimal import Decimal
from datetime import date
from .ReceiveIssueItem import ReceiveIssueItem


class ReceiveStockRequest(BaseModel):
    store_id: int
    date: date
    source_party: str
    remarks: str
    items: List[ReceiveIssueItem]