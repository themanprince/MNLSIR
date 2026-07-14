from pydantic import BaseModel

class UnitPayload(BaseModel):
    unit_id: int
    unit_name: str
    unit_symbol: str