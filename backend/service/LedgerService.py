# this service is for 'viewing'

from sqlalchemy.orm import Session
from sqlalchemy import select, asc, desc
from db import StockMovement, Product, StockBalance, Unit
from enum import Enum


class SortOrder(Enum):  # for selecting the order with which to sort stock balances from DB
    NO_ORDER = "NO_ORDER"
    ALPHABETICAL_ORDER = "ALPHABETICAL_ORDER"

SORT_MECHANISM = {  # mapping of SortOrder selection to sorting mechanism
    SortOrder.ALPHABETICAL_ORDER : Product.name.asc()
}

class LedgerService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_stock_balances(self, store_id: int, sort_order: SortOrder = SortOrder.ALPHABETICAL_ORDER, limit: int = 50, offset:int = 0):
        query = self.session.query(Product.id, Product.name, StockBalance.quantity, Unit.symbol)
        query = query.join(StockBalance).join(Product).join(Unit)
        query = query.filter(StockBalance.store_id == store_id)
        if sort_order and sort_order != SortOrder.NO_ORDER:
            query = query.order_by(SORT_MECHANISM[sort_order])
        query = query.offset(offset).limit(limit)
        result = query.all()

        return result


    def get_stock_movements(self, store_id: int, product_id: int, limit: int = 50, offset:int = 0, newest_first: bool = True):
        columns_to_order = [
            StockMovement.movement_date,
            StockMovement.created_at,
            StockMovement.id
        ]
        ordering = []
        if newest_first:
            ordering = [desc(x) for x in columns_to_order]
        else:
            ordering = [asc(x) for x in columns_to_order]
        
        statement = (
            select(StockMovement)
            .where(StockMovement.store_id == store_id, StockMovement.product_id == product_id)
            .order_by(*ordering)
            .limit(limit)
            .offset(offset)
        )
        result = self.session.execute(statement)
        
        return result.scalars().all()