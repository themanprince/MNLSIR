from fastapi import APIRouter, Depends, Body, HTTPException
from db import get_session
from schema.SubmitStockTakeIn import SubmitStockTakeIn
from service.InventoryService import InventoryService


InventoryRouter = APIRouter(prefix="/inventory")

@InventoryRouter.post("/stock-take", status_code=201)
async def submit_stock_take(stock_take_details: SubmitStockTakeIn = Body(), session = Depends(get_session)):
    try:
        inventory_service = InventoryService(session = session)
        inventory_service.submit_stocktake(**stock_take_details.model_dump())
        return {
            "status": "success",
            "msg": "stock take recorded successfully"
        }
    except Exception as e:
        raise  HTTPException(status_code=500, detail=str(e))