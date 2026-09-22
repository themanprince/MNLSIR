from sqladmin import expose
from starlette.requests import Request

from endpoints.helpers.stock_transaction_admin import (
    StockTransactionAdmin,
)
from schema.ReceiveIssueStockRequest import DispatchStockRequest
from service.InventoryService import InventoryService


class DispatchAdmin(StockTransactionAdmin):
    name = "Dispatch Stock"

    template_name = "dispatch.html"
    transaction_name = "Dispatch"

    @expose(
        "/dispatch",
        methods=["GET", "POST"],
    )
    async def dispatch(self, request: Request):
        return await self.handle_transaction(request)

    def _record(self, request, session, form):
        dispatch_date = self.parse_date(
            form.get("date"),
            "Dispatch date",
        )

        destination_vessel = str(
            form.get("destination_vessel") or ""
        ).strip()

        if not destination_vessel:
            raise ValueError(
                "Destination vessel is required."
            )

        payload = DispatchStockRequest(
            store_id=self.parse_positive_int(
                form.get("store_id"),
                "Store",
            ),
            date=dispatch_date,
            destination_vessel=destination_vessel,
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
        ).dispatch_stock(payload)