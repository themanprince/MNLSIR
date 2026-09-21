from sqlalchemy.orm import Session
from sqlalchemy import select
from db import Document, DocumentType, DocumentLine, StockMovement, MovementType, StockBalance, InterventionLog, ActionType, Store, Staff, Product
from schema.ReceiveIssueStockRequest import ReceiveIssueStockRequest, ReceiveStockRequest, IssueStockRequest, DispatchStockRequest
from service.UnitService import UnitService
from service.StockService import StockService
from exceptions import ReceiveIssueStockError
from exceptions import SubmitStockTakeError
from datetime import date
from decimal import Decimal


class InventoryService:
    def __init__(self, session: Session):
        self.session = session
        self.unit_service = UnitService(session=session)
        self.stock_service = StockService(session=session)
    
    
    def receive_issue_stock(self, payload: ReceiveStockRequest | IssueStockRequest):
        #this method was initially retained for backwards compatibility with code already using it... asides that, it is redundant to have a method whose only code is calling another method... lol
        return self._record_stock_document(payload)

    def dispatch_stock(self, payload: DispatchStockRequest):
        return self._record_stock_document(payload)

    def _record_stock_document(
        self,
        payload: ReceiveIssueStockRequest,
    ):
        self._validate_stock_document_payload(payload)

        if isinstance(payload, DispatchStockRequest):
            self._validate_dispatch_products(payload)

        document_type = self._get_document_type(payload)
        movement_type = self._get_movement_type(payload)
        quantity_sign = self._get_quantity_sign(payload)

        transaction_context = (
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )

        with transaction_context:
            document = Document(
                document_type=document_type,
                store_id=payload.store_id,
                date=payload.date,
                source_party=self._get_source_party(payload),
                destination_party=self._get_destination_party(payload),
                remarks=payload.remarks,
            )

            self.session.add(document)
            self.session.flush()

            product_ids = set()

            for item in payload.items:
                line_recorded_by = (
                    item.recorded_by
                    if item.recorded_by is not None
                    else payload.recorded_by
                )

                self._get_staff_or_raise(line_recorded_by)

                base_quantity = self.unit_service.to_base(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    from_unit_id=item.unit_id,
                )

                document_line = DocumentLine(
                    document_id=document.id,
                    product_id=item.product_id,
                    entered_quantity=item.quantity,
                    entered_unit_id=item.unit_id,
                    base_quantity=base_quantity,
                    recorded_by=line_recorded_by,
                )

                self.session.add(document_line)
                self.session.flush()

                movement = StockMovement(
                    recorded_by=line_recorded_by,
                    store_id=payload.store_id,
                    product_id=item.product_id,
                    document_line_id=document_line.id,
                    movement_type=movement_type,
                    quantity_delta=quantity_sign * base_quantity,
                    movement_date=payload.date,
                    remarks=payload.remarks,
                )

                self.session.add(movement)
                product_ids.add(item.product_id)

            self.session.flush()

            for product_id in product_ids:
                self.stock_service.recalculate(
                    store_id=payload.store_id,
                    product_id=product_id,
                    from_movement_date=payload.date,
                )

            return document

    @staticmethod
    def _validate_stock_document_payload(
        payload: ReceiveIssueStockRequest,
    ):
        if payload.date > date.today():
            raise ReceiveIssueStockError(
                "Please check date entered. "
                "Cannot receive, issue, or dispatch stock in the future."
            )

        if not payload.items:
            raise ReceiveIssueStockError(
                "No products were specified. "
                "Please specify products and quantities."
            )

        if any(item.quantity <= 0 for item in payload.items):
            raise ReceiveIssueStockError(
                "Quantities must be greater than zero."
            )

    @staticmethod
    def _validate_dispatch_products(
        payload: DispatchStockRequest,
    ):
        product_ids = [item.product_id for item in payload.items]
        duplicate_product_ids = {
            product_id
            for product_id in product_ids
            if product_ids.count(product_id) > 1
        }

        if duplicate_product_ids:
            duplicate_ids = ", ".join(
                str(product_id)
                for product_id in sorted(duplicate_product_ids)
            )

            raise ReceiveIssueStockError(
                "A dispatch cannot contain the same product more than once. "
                f"Duplicate product ID(s): {duplicate_ids}."
            )

        if not payload.destination_vessel.strip():
            raise ReceiveIssueStockError(
                "Destination vessel is required."
            )

    def _get_staff_or_raise(self, staff_id: int):
        staff = (
            self.session.query(Staff)
            .filter(Staff.id == staff_id)
            .first()
        )

        if not staff:
            raise ReceiveIssueStockError(
                f"Staff with id {staff_id} does not exist."
            )

        return staff

    @staticmethod
    def _get_document_type(
        payload: ReceiveIssueStockRequest,
    ) -> DocumentType:
        if isinstance(payload, ReceiveStockRequest):
            return DocumentType.GOODS_RECEIVED

        if isinstance(payload, DispatchStockRequest):
            return DocumentType.DISPATCH

        if isinstance(payload, IssueStockRequest):
            return DocumentType.ISSUE_RECORDS

        raise ReceiveIssueStockError(
            "Unsupported stock document type."
        )

    @staticmethod
    def _get_movement_type(
        payload: ReceiveIssueStockRequest,
    ) -> MovementType:
        if isinstance(payload, ReceiveStockRequest):
            return MovementType.RECIEVE

        return MovementType.ISSUE

    @staticmethod
    def _get_quantity_sign(
        payload: ReceiveIssueStockRequest,
    ) -> Decimal:
        if isinstance(payload, ReceiveStockRequest):
            return Decimal("1")

        return Decimal("-1")

    @staticmethod
    def _get_source_party(
        payload: ReceiveIssueStockRequest,
    ) -> str | None:
        if isinstance(payload, ReceiveStockRequest):
            return payload.source_party

        return None

    @staticmethod
    def _get_destination_party(
        payload: ReceiveIssueStockRequest,
    ) -> str | None:
        if isinstance(payload, IssueStockRequest):
            return payload.dest_party

        if isinstance(payload, DispatchStockRequest):
            return payload.destination_vessel

        return None

    def submit_stocktake(self, recorded_by:int, store_id: int, product_id: int, remarks: str, target_quantity: Decimal, target_unit_id: int | None = None, stocktake_date:date = date.today()) -> StockMovement:
        # this handles some scenarios as follows
        # 1. the scenario where store keeper needs to update digital stock balance of a product to align with its physical stock balance, in cases of observed but inexplainable discrepancies
        # 2. fresh inventory taking

        store = self.session.query(Store).filter(Store.id == store_id).first()
        if not store:
            raise SubmitStockTakeError(f"Store with id {store_id} does not exist")
        
        staff = self.session.query(Staff).filter(Staff.id == recorded_by).first()
        if not staff:
            raise SubmitStockTakeError(f"Staff with id {recorded_by} does not exist")
        
        product = self.session.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise SubmitStockTakeError(f"Product with id {product_id} does not exist")
        
        # If no unit is provided, preserve the existing behavior:
        # target_quantity is assumed to already be in the base unit.
        quantity_in_base_unit = target_quantity

        if target_unit_id is not None:
            try:
                quantity_in_base_unit = self.unit_service.to_base(
                product_id=product_id,
                    quantity=target_quantity,
                    from_unit_id=target_unit_id,
            )
            except Exception as error:
                raise SubmitStockTakeError(str(error)) from error
        
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
                target_quantity = quantity_in_base_unit,
                remarks = remarks,
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
                new_value_snapshot = quantity_in_base_unit,
                remarks = remarks
            )

            self.session.add(intervention_log)
            self.session.flush()

            self.stock_service.recalculate(store_id=store_id, product_id = product_id, from_movement_date = stocktake_date)

            return stock_movement
