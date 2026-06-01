from sqlalchemy import select
from sqlalchemy.orm import Session
from db import StockMovement, StockBalance, MovementType, InterventionLog, ActionType
from datetime import date
from decimal import Decimal
from exceptions import UpdateStockMovementError, AssociateStockMovementError
from typing import Optional
from enum import Enum


class AssociationMutationType(Enum): # for mutations to stocktake associations
    LINK = 1
    UNLINK = 2


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
            if movement.movement_type == MovementType.STOCKTAKE:
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
    

    def update_historical_stockmovement(self, movement_id:int, new_quantity_delta:Decimal, operator_name: str, remarks: str):
        # this allows store keepers to update a previously recorded stock movement..
        # the rurnning balances of stock movements following that one will be recalculated
        transaction_context = ( # if a transaction is already started, use a nested savepoint transaction. Otherwise, start a top-level transaction
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        with transaction_context:
            lock_statement = (
                select(StockMovement)
                .where(StockMovement.id == movement_id)
                .with_for_update()
            )
            self.session.execute(lock_statement)

            stock_movement = self.session.query(StockMovement).filter_by(id = movement_id).first()
            if not stock_movement:
                raise UpdateStockMovementError("Target stock movement record not found")
            
            old_quantity_delta = stock_movement.quantity_delta

            stock_movement.quantity_delta = new_quantity_delta

            intervention_log = InterventionLog(
                store_id = stock_movement.store_id,
                product_id = stock_movement.product_id,
                source_action_type = ActionType.IN_PLACE_EDIT,
                concerned_movement_id = stock_movement.id,
                old_value_snapshot = old_quantity_delta,
                new_value_snapshot = new_quantity_delta,
                changed_by = operator_name,
                remarks = remarks
            )

            self.session.add(intervention_log)
            self.session.flush()

            #StockBalance will be updated in recalculate() method
            self.recalculate(store_id=stock_movement.store_id, product_id=stock_movement.product_id, from_movement_date=stock_movement.movement_date)


 
    def insert_and_link_historical_movement(self, store_id: int, product_id: int, associated_stocktake_id:int, movement_type: MovementType, quantity_delta: Decimal, movement_date: date,  operator_name:str, remarks: Optional[str] = None) -> StockMovement:
        # stock takes refers to updates to StockBalance for a product that is usually not explainable by the StockMovement records for that product
        # (e.g. my stockmovement records say I should have 43tins of milk, but my physical inventory is 40tins of milk.. I'd have do a StockTake, recording 40tins as my new StockBalance),
        # since stock takes are usually initially inexplainable,
        # this method allows for linking stock_movements (discovered later on) that may help to explain a stock take, to that stock take
        transaction_context = (
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        with transaction_context:
            lock_statement = (
                select(StockMovement)
                .where(StockMovement.id == associated_stocktake_id)
                .with_for_update()
            )
            self.session.execute(lock_statement)
                        
            explanatory_stock_movement = StockMovement( #the linking to associated_stocktake_id will not be done in this method but in associate_stock_movement_to_stocktake(), where proper validation will be carried out before linking the stock movement records
                store_id = store_id,
                product_id = product_id,
                movement_type = movement_type,
                quantity_delta = quantity_delta,
                movement_date = movement_date,
                remarks = remarks if remarks else None
            )

            self.session.add(explanatory_stock_movement)
            self.session.flush()

            self.recalculate(store_id = store_id, product_id = product_id, from_movement_date = movement_date)
            
            self.associate_stock_movement_to_stocktake(movement_id = explanatory_stock_movement.id, stocktake_id=associated_stocktake_id, operator_name = operator_name)
            
            return explanatory_stock_movement


    def associate_stock_movement_to_stocktake(self, movement_id: int, stocktake_id: int, operator_name:str):
        # stock takes refers to updates to StockBalance for a product that is usually not explainable by the StockMovement records for that product
        # (e.g. my stockmovement records say I should have 43tins of milk, but my physical inventory is 40tins of milk.. I'd have do a StockTake, recording 40tins as my new StockBalance),
        # since stock takes are usually initially inexplainable,
        # this method allows for linking stock_movements that may help to explain a stock take, to that stock take
        self._mutate_stocktake_association(mutation_type=AssociationMutationType.LINK, movement_id = movement_id, stocktake_id = stocktake_id, operator_name=operator_name)
    

    def remove_association_from_stock_movement(self, movement_id:int, operator_name:str):
        self._mutate_stocktake_association(mutation_type=AssociationMutationType.UNLINK, movement_id = movement_id, operator_name = operator_name)


    def _mutate_stocktake_association(self, movement_id: int, operator_name: str, mutation_type: AssociationMutationType, stocktake_id:Optional[int] = None):
        # This method was created to apply DRY principle on certain methods.. thus, it may need to be evaluated in context to be understood i.e. in the context of the caller methtods
        # At the time of initial creation, it was meant to serve for both linking and unlinking stocktake records with other stockmovement records that helped explain them(the stocktakes)
        transaction_context = (
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        with transaction_context:
            lock_statement = (  # I'm locking only the explanatory StockMovement (instead of both it and the explained stock take) for two reasons.. 1. it is what is actually going to be modified in this methodd 2. this method may have been called by self.insert_and_link_historical_movement(). Thus, the explained stock_take may have already been locked in that method
                select(StockMovement)
                .where(StockMovement.id == movement_id)
                .with_for_update()
            )
            self.session.execute(lock_statement)
            
            stock_movement = self.session.query(StockMovement).filter_by(id = movement_id).first()
        
            if not stock_movement:
                raise AssociateStockMovementError(f"stock_movement with id={movement_id} does not exist")
            
            defualt_remark = None
            stocktake_to_associate_with = None # should be set only for mutation_type == AssociationMutationType.UNLINK

            if mutation_type == AssociationMutationType.UNLINK:
        
                if stock_movement.associated_stockmovement_id is None:
                    raise AssociateStockMovementError("Error removing association: stock_movement with id={stock_movement.id} has no associated_stockmovement")
                
                default_remark = f"Remove existing association between stocktake with id={stock_movement.associated_stockmovement_id} and stockmovement with id={stock_movement.id}"

            else:

                if not stocktake_id:
                    raise AssociateStockMovementError(f"Error creating association: stocktake_id not specified")

                stocktake_to_associate_with = self.session.query(StockMovement).filter_by(id = stocktake_id).first()

                if not stocktake_to_associate_with:
                    raise AssociateStockMovementError(f"Error creating association: stock_take with id={stocktake_id} does not exist")
                
                if stocktake_to_associate_with.movement_type != MovementType.STOCKTAKE:
                    raise AssociateStockMovementError(f"Error creating association: Target stock movement record with id={stocktake_to_associate_with.id} is not really a StockTake i.e. does not have movement_type=STOCKTAKE")

                if stock_movement.movement_date > stocktake_to_associate_with.movement_date:
                    raise AssociateStockMovementError(f"Error creating association: Invalid date.. explanatory Stock movement cannot have date later than stock_take to be explained")
                
                default_remark = f"Partly / Fully Explaining stock-take with id={stocktake_to_associate_with.id} using stockmovement with id={stock_movement.id}"
                
                
            stock_movement.associated_stockmovement_id = stocktake_to_associate_with.id if stocktake_to_associate_with else None  # this should set this property to None if mutation_type == AssociationMutationType.UNLINK

            intervention_log = InterventionLog(
                store_id = stock_movement.store_id,
                product_id = stock_movement.product_id,
                source_action_type = ActionType.REMOVE_ASSOCIATION if mutation_type == AssociationMutationType.UNLINK else ActionType.EXPLAIN_DISCREPANCY,
                concerned_movement_id = stock_movement.id,
                new_value_snapshot = -1,
                changed_by = operator_name,
                remarks = default_remark
            )

            self.session.add(intervention_log)
            self.session.flush()
        
