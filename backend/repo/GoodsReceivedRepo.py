from sqlalchemy.orm import Session, selectinload

from db import (
    Document,
    DocumentLine,
    DocumentType,
)


class GoodsReceivedRepo:
    @staticmethod
    def get_for_store(
        session: Session,
        store_id: int,
    ) -> list[Document]:
        return (
            session.query(Document)
            .options(
                selectinload(Document.store),
                selectinload(Document.lines)
                .selectinload(DocumentLine.product),
                selectinload(Document.lines)
                .selectinload(DocumentLine.entered_unit),
                selectinload(Document.lines)
                .selectinload(DocumentLine.recorder),
            )
            .filter(
                Document.store_id == store_id,
                Document.document_type == DocumentType.GOODS_RECEIVED,
            )
            .order_by(
                Document.date.asc(),
                Document.created_at.asc(),
                Document.id.asc(),
            )
            .all()
        )