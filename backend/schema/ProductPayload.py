from pydantic import BaseModel
from typing import List
from .UnitConversionRule import UnitConversionRule


class ProductPayload(BaseModel):
    base_unit_id: int
    name: str
    sku: str
    unit_conversions: List[UnitConversionRule]

    model_config = {
        "from_attributes": True
    }