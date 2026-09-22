from sqladmin import expose
from starlette.requests import Request
from db import DocumentType
from endpoints.helpers.stock_document_ledger import StockDocumentLedgerAdmin



class DispatchLedgerAdmin(
    StockDocumentLedgerAdmin
):
    name = "Dispatch Ledger"

    document_type = DocumentType.DISPATCH
    page_title = "Dispatch Ledger"
    page_description = (
        "View products dispatched from a store."
    )
    party_label = "Destination Vessel"
    party_attribute = "destination_party"
    empty_message = (
        "No dispatches have been recorded "
        "for this store."
    )

    @expose(
        "/dispatch-ledger",
        methods=["GET"],
    )
    async def dispatch_ledger(
        self,
        request: Request,
    ):
        return await self._display_ledger(request)