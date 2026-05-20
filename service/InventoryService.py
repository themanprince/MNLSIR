from sqlalchemy.orm import Session
from sqlalchemy import select
from db import Document, DocumentType, DocumentLine, StockMovement, MovementType, StockBalance, InterventionLog, ActionType
from schema.ReceiveStockRequest import ReceiveStockRequest
from service.UnitService import UnitService
from service.StockService import StockService
from exceptions import ReceiveStockError
from datetime import date
from decimal import Decimal


class InventoryService:
    def __init__(self, session: Session):
        self.session = session
        self.unit_service = UnitService(session=session)
        self.stock_service = StockService(session=session)
    

    def receive_stock(self, payload: ReceiveStockRequest):
        if payload.date > date.today():
            raise ReceiveStockError("Please check date entered. Cannot Receive Stock in the future")
        
        if any([item.quantity <= 0 for item in payload.items]):
            raise ReceiveStockError("Please check quantities of items to Receive. Cannot have zero(0) or -negative quantity")

        if not payload.items:
            raise ReceiveStockError("No products were specified for receiving. Please specify products/quantities to receive")

        transaction_context = ( # if a transaction is already started, use a nested savepoint transaction. Otherwise, start a top-level transaction
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        with transaction_context: #transaction
            document = Document(
                document_type = DocumentType.GOODS_RECEIVED,
                store_id = payload.store_id,
                date = payload.date,
                source_party = payload.source_party,
                remarks = payload.remarks
            )

            self.session.add(document)
            self.session.flush()

            for item in payload.items:

                base_quantity = self.unit_service.to_base(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    from_unit_id=item.unit_id
                )

                document_line = DocumentLine(
                    document_id = document.id,
                    product_id = item.product_id,
                    entered_quantity = item.quantity,
                    entered_unit_id = item.unit_id,
                    base_quantity = base_quantity
                )

                self.session.add(document_line)
                self.session.flush()

                movement =  StockMovement(
                    store_id = payload.store_id,
                    product_id = item.product_id,
                    document_line_id = document_line.id,
                    movement_type = MovementType.RECIEVE,
                    quantity_delta = base_quantity,
                    movement_date = payload.date
                )

                self.session.add(movement)
                self.session.flush()

                self.stock_service.recalculate(
                    store_id=payload.store_id,
                    product_id = item.product_id,
                    from_movement_date=payload.date
                )

            return document
    

    def submit_stocktake(self, store_id: int, product_id: int, target_quantity: Decimal, operator_name: str, remarks: str, stocktake_date:date = date.today()):
        # this handles some scenarios as follows
        # 1. the scenario where store keeper needs to update digital stock balance of a product to align with its physical stock balance, in cases of observed but inexplainable discrepancies
        # 2. fresh inventory taking
        transaction_context = ( # if a transaction is already started, use a nested savepoint transaction. Otherwise, start a top-level transaction
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        with transaction_context:
            lock_statement = ( #so nobody updates StockBalance while I'm still working with it
                select(StockBalance)
                .where(StockBalance.store_id == store_id, StockBalance.product_id == product_id)
                .with_for_update()
            )
            self.session.execute(lock_statement)

            current_balance_record = self.session.query(StockBalance).filter(StockBalance.store_id == store_id, StockBalance.product_id == product_id).first()
            current_quantity = current_balance_record.quantity if current_balance_record else Decimal("0")

            action_type = ActionType.INITIAL_STOCK_TAKE if current_balance_record is None else ActionType.BALANCE_OVERWRITE_RECONCILE

            stock_movement = StockMovement(
                store_id = store_id,
                product_id = product_id,
                movement_type = MovementType.ADJUST,
                quantity_delta = Decimal("0"), # this is an adjustment stock movement.. the stock balance should be changed to the set target_quantity, and not be calculated based on some quantity_delta
                target_quantity = target_quantity,
                movement_date = stocktake_date #explicitly passed, as guard against delayed submissions
            )

            self.session.add(stock_movement)
            self.session.flush()

            #logging the action into out audit trail
            intervention_log = InterventionLog(
                store_id = store_id,
                product_id = product_id,
                action_type = action_type,
                concerned_movement_id = stock_movement.id,
                old_value_snapshot = current_quantity,
                new_value_snapshot = target_quantity,
                changed_by = operator_name,
                remarks = remarks
            )

            self.session.add(intervention_log)
            self.session.flush()

            self.stock_service.recalculate(store_id=store_id, product_id = product_id, from_movement_date = stocktake_date)
    

    