from sqlalchemy.orm import Session

from db import Document, DocumentType


class StockDocumentLedgerRepo:
    @staticmethod
    def get_for_store(
        session: Session,
        store_id: int,
        document_type: DocumentType,
    ):
        return (
            session.query(Document)
            .filter(
                Document.store_id == store_id,
                Document.document_type == document_type,
            )
            .order_by(
                Document.date.desc(),
                Document.created_at.desc(),
                Document.id.desc(),
            )
            .all()
        )