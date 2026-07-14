from fastapi import APIRouter, Depends, Body, HTTPException
from db import get_session
from repo.StoreRepo import StoreRepo
from schema.CreateStoreResponse import CreateStoreResponse


StoreRouter = APIRouter(prefix="/store")

@StoreRouter.post("/{store_name}", response_model = CreateStoreResponse, status_code=201)
async def create_store(store_name, session = Depends(get_session)):
    try:
        store_details = StoreRepo.create_new_store(store_name = store_name, session = session)
        return store_details
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@StoreRouter.get("/all")
async def get_all_stores(session = Depends(get_session)):
    try:
        return StoreRepo.get_all_stores(session = session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))