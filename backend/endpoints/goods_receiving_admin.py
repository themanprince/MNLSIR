from sqladmin import BaseView, expose
from starlette.requests import Request
from starlette.responses import RedirectResponse
from datetime import date
from decimal import InvalidOperation
from db import Store
from db import make_session
from auth import is_logged_in
from service.InventoryService import InventoryService
from schema.ReceiveIssueStockRequest import ReceiveStockRequest
from endpoints.helpers.stock_transaction_form import StockTransactionForm



class GoodsReceivingAdmin(BaseView):
    name = "Receive Goods"
    
    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)
    
    
    async def _render(
        self,
        request: Request,
        session,
        *,
        message: str | None = None,
        message_type: str = "info",
        form_data: dict | None = None,
    ):
        context = StockTransactionForm.get_form_data(
            session
        )

        StockTransactionForm.add_render_context(
            context,
            request,
            message=message,
            message_type=message_type,
            form_data=form_data,
        )

        return await self.templates.TemplateResponse(
            request,
            "goods_receiving.html",
            context,
        )
    

    @expose("/goods-receiving", methods=["GET", "POST"])
    async def goods_receiving(self, request: Request):
        session = make_session()

        try:
            if request.method == "GET":
                return await self._render(request, session)

            staff_id = (
                StockTransactionForm
                .get_authenticated_staff_id(request)
            )
            form = await request.form()

            store_id = StockTransactionForm.parse_positive_int(
                form.get("store_id"),
                "Store",
            )

            transaction_date = str(form.get("date"))
            if not transaction_date:
                raise ValueError("Receiving date is required.")

            try:
                receiving_date = date.fromisoformat(transaction_date)
            except ValueError:
                raise ValueError("Receiving date is invalid.")

            source_party = (str(form.get("source_party")) or "").strip()
            if not source_party:
                raise ValueError("Source party is required.")

            remarks = (str(form.get("remarks")) or "").strip()

            items = StockTransactionForm.parse_items(form)
            store = session.query(Store).filter_by(id=store_id).first()
            if not store:
                raise ValueError("The selected store does not exist.")

            payload = ReceiveStockRequest(
                store_id=store_id,
                date=receiving_date,
                source_party=source_party,
                remarks=remarks,
                recorded_by=staff_id,
                items=items,
            )

            inventory_service = InventoryService(session=session)

            document = inventory_service.receive_issue_stock(payload)

            # Queries performed while loading the form start a SQLAlchemy
            # transaction. Commit explicitly so the successful save persists.
            session.commit()

            return await self._render(
                request,
                session,
                message=(
                    f"Goods receiving transaction #{document.id} "
                    "was recorded successfully."
                ),
                message_type="success",
            )

        except PermissionError as error:
            session.rollback()

            return RedirectResponse(
                url="/admin/login",
                status_code=303,
            )

        except (ValueError, InvalidOperation) as error:
            session.rollback()

            form_data = {
                "store_id": request.query_params.get("store_id", ""),
            }

            return await self._render(
                request,
                session,
                message=str(error),
                message_type="danger",
                form_data=form_data,
            )

        except Exception:
            session.rollback()

     
            return await self._render(
                request,
                session,
                message=(
                    "The goods receiving transaction could not be recorded. "
                    "Please try again or contact an administrator."
                ),
                message_type="danger",
            )

        finally:
            session.close()


