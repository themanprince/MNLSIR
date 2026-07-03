from pydantic import BaseModel

class CreateStoreResponse(BaseModel):
    store_id: int
    store_name: str