import logging

from sqladmin import BaseView
from starlette.requests import Request

from auth import is_logged_in
from db import DocumentType, Store, make_session
from repo.StockDocumentLedgerRepo import StockDocumentLedgerRepo


logger = logging.getLogger(__name__)


class StockDocumentLedgerAdmin(BaseView):
    """
    Shared implementation for document-based stock ledgers.

    Concrete ledger classes only configure:
    - document type
    - page name
    - page title
    - party label
    - party attribute
    - empty-state message
    - route
    """

    document_type: DocumentType
    page_title: str
    page_description: str
    party_label: str
    party_attribute: str
    empty_message: str
    template_name = "stock_document_ledger.html"

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

    @staticmethod
    def _get_stores(session):
        return (
            session.query(Store)
            .order_by(Store.name.asc())
            .all()
        )

    @staticmethod
    def _parse_store_id(store_id_value):
        try:
            store_id = int(store_id_value)
        except (TypeError, ValueError):
            raise ValueError(
                "The selected store is invalid."
            )

        if store_id <= 0:
            raise ValueError(
                "The selected store is invalid."
            )

        return store_id

    def _get_selected_store(
        self,
        session,
        store_id_value,
    ):
        if not store_id_value:
            return None

        store_id = self._parse_store_id(
            store_id_value
        )

        selected_store = (
            session.query(Store)
            .filter(Store.id == store_id)
            .first()
        )

        if not selected_store:
            raise ValueError(
                "The selected store does not exist."
            )

        return selected_store

    def _get_documents(
        self,
        session,
        selected_store,
    ):
        if not selected_store:
            return []

        return StockDocumentLedgerRepo.get_for_store(
            session=session,
            store_id=selected_store.id,
            document_type=self.document_type,
        )

    async def _render_ledger(
        self,
        request: Request,
        *,
        stores,
        selected_store=None,
        documents=None,
        message=None,
        message_type="info",
    ):
        return await self.templates.TemplateResponse(
            request,
            self.template_name,
            {
                "request": request,
                "stores": stores,
                "selected_store": selected_store,
                "documents": documents or [],
                "message": message,
                "message_type": message_type,
                "page_title": self.page_title,
                "page_description": self.page_description,
                "party_label": self.party_label,
                "party_attribute": self.party_attribute,
                "empty_message": self.empty_message,
            },
        )

    async def _display_ledger(self, request: Request):
        session = make_session()

        try:
            stores = self._get_stores(session)

            store_id_value = request.query_params.get(
                "store_id"
            )

            selected_store = self._get_selected_store(
                session,
                store_id_value,
            )

            documents = self._get_documents(
                session,
                selected_store,
            )

            return await self._render_ledger(
                request,
                stores=stores,
                selected_store=selected_store,
                documents=documents,
            )

        except ValueError as error:
            session.rollback()

            return await self._render_ledger(
                request,
                stores=self._get_stores(session),
                message=str(error),
                message_type="danger",
            )

        except Exception:
            session.rollback()

            logger.exception(
                "Unable to load %s ledger.",
                self.page_title,
            )

            return await self._render_ledger(
                request,
                stores=[],
                message=(
                    f"The {self.page_title.lower()} could not "
                    "be loaded. Please try again."
                ),
                message_type="danger",
            )

        finally:
            session.close()
