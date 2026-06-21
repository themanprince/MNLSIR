from sqlalchemy.orm import Session
from sqlalchemy import select
from db import Document, DocumentType, DocumentLine, StockMovement, MovementType, StockBalance, InterventionLog, ActionType
from schema.ReceiveIssueStockRequest import ReceiveStockRequest, IssueStockRequest
from service.UnitService import UnitService
from service.StockService import StockService
from exceptions import ReceiveIssueStockError
from datetime import date
from decimal import Decimal


class InventoryService:
    def __init__(self, session: Session):
        self.session = session
        self.unit_service = UnitService(session=session)
        self.stock_service = StockService(session=session)
    
    
    def receive_issue_stock(self, payload: ReceiveStockRequest | IssueStockRequest):
        if payload.date > date.today():
            raise ReceiveIssueStockError("Please check date entered. Cannot Receive/Issue Stock in the future")
        
        if any([item.quantity <= 0 for item in payload.items]):
            raise ReceiveIssueStockError("Please check quantities of items to Receive/Issue. Cannot have zero(0) or -negative quantity")

        if not payload.items:
            raise ReceiveIssueStockError("No products were specified for receiving/issuing. Please specify products/quantities to receive")

        transaction_context = ( # if a transaction is already started, use a nested savepoint transaction. Otherwise, start a top-level transaction
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        with transaction_context: #transaction
            document = Document(
                document_type = DocumentType.GOODS_RECEIVED if isinstance(payload, ReceiveStockRequest) else DocumentType.ISSUE_RECORDS,
                store_id = payload.store_id,
                date = payload.date,
                source_party = payload.source_party if isinstance(payload, ReceiveStockRequest) else None,
                destination_party = payload.dest_party if isinstance(payload, IssueStockRequest) else None,
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

                """
                # I commented out this code to allow issuing even on insufficient quantities. Here's why..
                # Sometimes, physical inventory may not agree with records on the software.
                # For instance, a scenario where the physical inventory is sufficient but the software's inventory is not.
                # Such scenario may result from improper recording in the past, which could be fixed later on by the user.
                # However, it should not lead to loss of present records which could result if the present issuing is prevented
                # due to insufficient quantity according to the software's records.
                
                if isinstance(payload, IssueStockRequest):
                    product_balance = self.session.query(StockBalance).filter_by(
                        store_id = payload.store_id, product_id = item.product_id
                    ).with_for_update().one_or_none()
                    
                    qty_avail = product_balance.quantity if product_balance else 0
                    
                    if qty_avail - base_quantity < 0:
                        raise ReceiveIssueStockError(f"Cannot issue product with id {item.product_id}. Insufficient Quantity Available in store")
                """

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
                    recorded_by = payload.recorded_by,
                    store_id = payload.store_id,
                    product_id = item.product_id,
                    document_line_id = document_line.id,
                    movement_type = MovementType.RECIEVE if isinstance(payload, ReceiveStockRequest) else MovementType.ISSUE,
                    quantity_delta = base_quantity if isinstance(payload, ReceiveStockRequest) else -base_quantity,
                    movement_date = payload.date
                )

                self.session.add(movement)
            
            # advised to put these outside the loop for performance reasons
            self.session.flush()

            for item in payload.items:
                self.stock_service.recalculate(
                    store_id=payload.store_id,
                    product_id = item.product_id,
                    from_movement_date=payload.date
                )

            return document
    


    def submit_stocktake(self, recorded_by:int, store_id: int, product_id: int, target_quantity: Decimal, remarks: str, stocktake_date:date = date.today()) -> StockMovement:
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
                recorded_by = recorded_by,
                store_id = store_id,
                product_id = product_id,
                movement_type = MovementType.STOCKTAKE,
                quantity_delta = Decimal("0"), # this is an adjustment stock movement.. the stock balance should be changed to the set target_quantity, and not be calculated based on some quantity_delta
                target_quantity = target_quantity,
                movement_date = stocktake_date #explicitly passed, as guard against delayed submissions
            )

            self.session.add(stock_movement)
            self.session.flush()

            #logging the action into out audit trail
            intervention_log = InterventionLog(
                recorded_by = recorded_by,
                store_id = store_id,
                product_id = product_id,
                source_action_type = action_type,
                concerned_movement_id = stock_movement.id,
                old_value_snapshot = current_quantity,
                new_value_snapshot = target_quantity,
                remarks = remarks
            )

            self.session.add(intervention_log)
            self.session.flush()

            self.stock_service.recalculate(store_id=store_id, product_id = product_id, from_movement_date = stocktake_date)

            return stock_movement