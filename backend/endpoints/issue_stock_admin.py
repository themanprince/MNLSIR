from sqladmin import expose
from starlette.requests import Request

from endpoints.helpers.stock_transaction_admin import (
    StockTransactionAdmin,
)
from schema.ReceiveIssueStockRequest import IssueStockRequest
from service.InventoryService import InventoryService


class IssueStockAdmin(StockTransactionAdmin):
    name = "Issue Stock"

    template_name = "issue_stock.html"
    transaction_name = "Issue record"

    @expose(
        "/issue-stock",
        methods=["GET", "POST"],
    )
    async def issue_stock(self, request: Request):
        return await self.handle_transaction(request)

    def _record(self, request, session, form):
        issue_date = self.parse_date(
            form.get("date"),
            "Issue date",
        )

        destination_party = str(
            form.get("dest_party") or ""
        ).strip()

        if not destination_party:
            raise ValueError(
                "Destination party is required."
            )

        payload = IssueStockRequest(
            store_id=self.parse_positive_int(
                form.get("store_id"),
                "Store",
            ),
            date=issue_date,
            dest_party=destination_party,
            remarks=str(
                form.get("remarks") or ""
            ).strip(),
            recorded_by=self.get_authenticated_staff_id(
                request
            ),
            items=self.parse_items(form),
        )

        return InventoryService(
            session=session
        ).receive_issue_stock(payload)