from pydantic import BaseModel
from typing import List
from .UnitConversionRule import UnitConversionRule


class ProductPayload(BaseModel):
    id: int
    name: str
    sku: str
    base_unit_id: int
    unit_conversions: List[UnitConversionRule]

    model_config = {
        "from_attributes": True
    }