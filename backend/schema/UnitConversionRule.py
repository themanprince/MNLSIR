from pydantic import BaseModel
from decimal import Decimal

class UnitConversionRule(BaseModel):
    unit_id: int
    multiplier_to_base: Decimal