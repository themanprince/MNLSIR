from fastapi import APIRouter, Depends, Body, HTTPException
from db import get_session
from service.repo.StoreRepo import StoreRepo


StoreRouter = APIRouter(prefix="/store")

@StoreRouter.post("/{store_name}", status_code=201)
async def create_store(store_name, session = Depends(get_session)):
    try:
        store = StoreRepo.create_new_store(store_name = store_name, session = session)
        return {"store_id": store.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))