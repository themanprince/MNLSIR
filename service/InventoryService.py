from sqlalchemy.orm import Session
from db import Document, DocumentType, DocumentLine, StockMovement, MovementType
from schema.ReceiveStockRequest import ReceiveStockRequest
from service.UnitService import UnitService
from service.StockService import StockService


class InventoryService:
    def __init__(self, session: Session):
        self.session = session
        self.unit_service = UnitService(session=session)
        self.stock_service = StockService(session=session)
    

    def receive_stock(self, payload: ReceiveStockRequest):
        with self.session.begin(): #transaction
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