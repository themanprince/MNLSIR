from pydantic import BaseModel
from decimal import Decimal


class ReceiveIssueItem(BaseModel):
    product_id: int
    unit_id: int
    quantity: Decimal
    # Optional because normal UI submissions use the authenticated
    # staff member from the parent request.
    recorded_by: int | None = None