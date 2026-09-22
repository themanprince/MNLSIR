from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import RedirectResponse
from datetime import date
from decimal import InvalidOperation
from db import make_session
from auth import is_logged_in
from service.InventoryService import InventoryService
from schema.ReceiveIssueStockRequest import DispatchStockRequest
from endpoints.helpers.stock_transaction_form import StockTransactionForm
from exceptions import ReceiveIssueStockError



class DispatchAdmin(BaseView):
    name = "Dispatch Stock"

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

    async def _render_dispatch(
        self,
        request: Request,
        session,
        *,
        message: str | None = None,
        message_type: str = "info",
        form_data: dict | None = None,
    ):
        """
        Render the dispatch form using shared stock transaction data.
        """

        context = StockTransactionForm.get_form_data(session)

        StockTransactionForm.add_render_context(
            context,
            request,
            message=message,
            message_type=message_type,
            form_data=form_data,
        )

        return await self.templates.TemplateResponse(
            request,
            "dispatch.html",
            context,
        )

    @expose("/dispatch", methods=["GET", "POST"])
    async def dispatch(self, request: Request):
        session = make_session()

        try:
            if request.method == "GET":
                return await self._render_dispatch(
                    request,
                    session,
                )

            staff_id = (
                StockTransactionForm
                .get_authenticated_staff_id(request)
            )

            form = await request.form()

            store_id = StockTransactionForm.parse_positive_int(
                form.get("store_id"),
                "Store",
            )

            dispatch_date_value = str(form.get("date"))

            if not dispatch_date_value:
                raise ValueError(
                    "Dispatch date is required."
                )

            try:
                dispatch_date = date.fromisoformat(
                    dispatch_date_value
                )
            except ValueError:
                raise ValueError(
                    "Dispatch date is invalid."
                )

            destination_vessel = (
                str(form.get("destination_vessel")) or ""
            ).strip()

            remarks = (
                str(form.get("remarks")) or ""
            ).strip()

            items = StockTransactionForm.parse_items(form)

            payload = DispatchStockRequest(
                store_id=store_id,
                date=dispatch_date,
                destination_vessel=destination_vessel,
                remarks=remarks,
                recorded_by=staff_id,
                items=items,
            )

            document = InventoryService(
                session=session
            ).dispatch_stock(payload)

            session.commit()

            return await self._render_dispatch(
                request,
                session,
                message=(
                    f"Dispatch #{document.id} "
                    "was recorded successfully."
                ),
                message_type="success",
            )

        except PermissionError:
            session.rollback()

            return RedirectResponse(
                url="/admin/login",
                status_code=303,
            )

        except (
            ValueError,
            InvalidOperation,
            ReceiveIssueStockError,
        ) as error:
            session.rollback()

            return await self._render_dispatch(
                request,
                session,
                message=str(error),
                message_type="danger",
            )

        except Exception:
            session.rollback()

            return await self._render_dispatch(
                request,
                session,
                message=(
                    "The dispatch could not be recorded. "
                    "Please try again or contact an administrator."
                ),
                message_type="danger",
            )

        finally:
            session.close()
