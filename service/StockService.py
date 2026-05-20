from sqlalchemy import select
from sqlalchemy.orm import Session
from db import StockMovement, StockBalance, MovementType
from datetime import date
from decimal import Decimal


class StockService:
    def __init__(self, session: Session):
        self.session = session
    
    def recalculate(self, store_id: int, product_id: int, from_movement_date: date):
        #this method helps to recompute the stock movement records of a product in a given store
        # this is needed after operations that insert new stock movement records, especially the ones that back-date   
        lock_statement = (
            select(StockMovement)
            .where(
                StockMovement.store_id == store_id,
                StockMovement.product_id == product_id
            )
            .with_for_update() # POV: you're locking all movements for this store-product so no concurrent-writes messes stuff up (in that tiktok voice)
        )

        self.session.execute(lock_statement)

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
            if movement.movement_type == MovementType.ADJUST:
                running_balance = movement.target_quantity #reset running balance to the value adjusted to
            else:
                running_balance += movement.quantity_delta #regular issue/receipt
    
            movement.running_balance = running_balance
        
        stock_balance = (
            self.session.query(StockBalance)
            .filter(
                StockBalance.product_id == product_id,
                StockBalance.store_id == store_id
            )
            .first()
        )

        if stock_balance is None:
            stock_balance = StockBalance(
                store_id = store_id,
                product_id = product_id,
                quantity = running_balance
            )

            self.session.add(stock_balance)
            self.session.flush()
        else:
            stock_balance.quantity = running_balance