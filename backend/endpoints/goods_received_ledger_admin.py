from sqladmin import expose
from starlette.requests import Request
from db import DocumentType
from endpoints.helpers.stock_document_ledger import StockDocumentLedgerAdmin



class GoodsReceivedLedgerAdmin(
    StockDocumentLedgerAdmin
):
    name = "Goods Received Ledger"

    document_type = DocumentType.GOODS_RECEIVED
    page_title = "Goods Received Ledger"
    page_description = (
        "View products received into a store."
    )
    party_label = "Source"
    party_attribute = "source_party"
    empty_message = (
        "No goods received have been recorded "
        "for this store."
    )

    @expose(
        "/goods-received-ledger",
        methods=["GET"],
    )
    async def goods_received_ledger(
        self,
        request: Request,
    ):
        return await self._display_ledger(request)
