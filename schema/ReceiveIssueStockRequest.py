from pydantic import BaseModel
from typing import List
from decimal import Decimal
from datetime import date
from .ReceiveIssueItem import ReceiveIssueItem


class ReceiveIssueStockRequest(BaseModel):
    store_id: int
    date: date
    remarks: str
    items: List[ReceiveIssueItem]

class ReceiveStockRequest(ReceiveIssueStockRequest):
    source_party: str

class IssueStockRequest(ReceiveIssueStockRequest):
    dest_party: str
