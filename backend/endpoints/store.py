from fastapi import APIRouter, Depends, Body
from db import get_session
from service.repo.StoreRepo import StoreRepo

StoreRouter = APIRouter(prefix="/store")

@StoreRouter.post("/", status_code=201)
async def create_store(store_name = Depends(Body(embed=True)), session = Depends(get_session)):
    store = StoreRepo.create_new_store(store_name = store_name, session = session)
    return store.id