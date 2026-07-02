from fastapi import APIRouter, Depends, HTTPException
from db import get_session
from schema.StockBalance import StockBalanceOut
from service.LedgerService import LedgerService, SortOrder


LedgerRouter  = APIRouter(prefix="/ledger")

stock_balances_sort_order_text_mapping = {
    "alpha": SortOrder.ALPHABETICAL_ORDER
}

@LedgerRouter.get("/stock-balances/{store_id}", response_model=StockBalanceOut)
async def stock_balances(store_id: int, sort:str = "alpha", offset: int = 0, limit: int = 50, session = Depends(get_session)):
    try:
        ledger = LedgerService(session = session)
        sort_order = SortOrder.NO_ORDER
        if sort and sort in stock_balances_sort_order_text_mapping:
            sort_order = stock_balances_sort_order_text_mapping[sort]
        
        return {
            "items" : ledger.get_stock_balances(store_id = store_id, sort_order = sort_order, limit = limit, offset = offset)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))