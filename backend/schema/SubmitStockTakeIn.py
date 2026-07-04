from pydantic import BaseModel
from decimal import Decimal
from typing import Optional
from datetime import date

class SubmitStockTakeIn(BaseModel):
    recorded_by: int #staff_id of staff who handled the software to create this entry
    store_id: int
    product_id: int
    target_quantity: Decimal
    remarks: str
    stocktake_date: Optional[date] = date.today()