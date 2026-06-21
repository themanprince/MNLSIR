from pydantic import BaseModel
from decimal import Decimal


class ReceiveIssueItem(BaseModel):
    product_id: int
    unit_id: int
    quantity: Decimal