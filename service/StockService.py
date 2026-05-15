from sqlalchemy import select
from sqlalchemy.orm import Session
from db import StockMovement, StockBalance
from datetime import datetime
from decimal import Decimal


class StockService:
    def __init__(self, session: Session):
        self.session = session
    
    def recalculate(self, store_id: int, product_id: int, from_movement_date: datetime):
                
        statement = (
            select(StockMovement)
            .where(
                StockMovement.store_id == store_id,
                StockMovement.product_id == product_id
            )
            .order_by(
                StockMovement.movement_date.asc(),
                StockMovement.created_at.asc(),
                StockMovement.id.asc()
            )
            .with_for_update() # POV: you're locking all movements for this store-product so no concurrent-writes messes stuff up (in that tiktok voice)
        )

        self.session.execute(statement)

        movements = (
            self.session.query(StockMovement)
            .filter(
                StockMovement.movement_date >= from_movement_date, # but for performance sakes, I'm not goin' to work with all movements for this store-product
                StockMovement.store_id == store_id,
                StockMovement.product_id == product_id
            )
            .order_by(
                StockMovement.movement_date.asc(),
                StockMovement.created_at.asc(),
                StockMovement.id.asc()
            )
            .all()
        )

        previous_movement = (
            self.session.query(StockMovement)
            .filter(
                StockMovement.movement_date < from_movement_date,
                StockMovement.store_id == store_id,
                StockMovement.product_id == product_id
            )
            .order_by(
                StockMovement.movement_date.desc(),
                StockMovement.created_at.desc(),
                StockMovement.id.desc()
            )
            .first()
        )

        running_balance = (
            previous_movement.running_balance
            if previous_movement
            else Decimal("0")
        )

        for movement in movements:
            running_balance += movement.quantity_delta
            movement.running_balance = running_balance
        
        stock_balance = (
            self.session.query(StockBalance)
            .filter(
                StockBalance.product_id == product_id
            )
            .first()
        )

        if stock_balance is None:
            stock_balance = StockBalance(
                product_id = product_id,
                quantity = running_balance
            )

            self.session.add(StockBalance)
        else:
            stock_balance.quantity = running_balance