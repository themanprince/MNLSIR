# this service is for 'viewing'

from sqlalchemy.orm import Session
from sqlalchemy import select, asc, desc
from db import StockMovement

class LedgerService:
    def __init__(self, session: Session):
        self.session = session
    
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