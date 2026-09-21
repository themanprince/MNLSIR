from sqladmin import ModelView, BaseView, expose
from sqladmin.filters import ForeignKeyFilter
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import RedirectResponse
from wtforms import PasswordField
from wtforms.validators import Regexp
from datetime import date
from decimal import Decimal, InvalidOperation
import logging
from db import Unit, Product, Store, ProductUnitConversion, Staff, StockMovement
from db import make_session
from auth import is_logged_in, is_admin, get_password_hash, decode_access_token
from repo.StoreRepo import StoreRepo
from repo.ProductRepo import ProductRepo
from repo.GoodsReceivedRepo import GoodsReceivedRepo
from service.LedgerService import LedgerService, SortOrder
from service.InventoryService import InventoryService
from schema.ReceiveIssueItem import ReceiveIssueItem
from schema.ReceiveIssueStockRequest import ReceiveStockRequest, DispatchStockRequest
from endpoints.helpers.stock_transaction_form import StockTransactionForm
from exceptions import ReceiveIssueStockError



logger = logging.getLogger(__name__)


class UnitAdmin(ModelView, model=Unit):
    column_list = [Unit.id, Unit.name, Unit.symbol]
    column_searchable_list = [Unit.name, Unit.symbol]
    column_sortable_list = [Unit.name, Unit.symbol]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)   


class ProductAdmin(ModelView, model=Product):
    column_list = [Product.name, Product.sku, Product.base_unit]
    form_columns = [Product.name, Product.sku, Product.base_unit]
    column_searchable_list = [Product.sku, Product.name]
    column_sortable_list = [Product.sku, Product.name]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)


class StoreAdmin(ModelView, model=Store):
    column_list = [Store.name]
    form_columns = [Store.name]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)


class ProductUnitConversionAdmin(ModelView, model=ProductUnitConversion):
    column_list = [ProductUnitConversion.product, ProductUnitConversion.unit, ProductUnitConversion.multiplier_to_base]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)


class InventoryAdmin(BaseView):
    name = "Inventory"

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

    @expose("/inventory", methods=["GET", "POST"])
    async def get_inventory_view(self, request):
        session = make_session()

        async def return_template_with_info(message, products, stores, product_units):
            return await self.templates.TemplateResponse(request, "inventory.html", {"message": message, "products": products, "stores": stores, "product_units": product_units})

        try:
            products = await run_in_threadpool(ProductRepo(session = session).get_all_products)
            stores = await run_in_threadpool(StoreRepo.get_all_stores, session = session)
            conversions = await run_in_threadpool(
                lambda: session.query(ProductUnitConversion)
                .join(Unit, ProductUnitConversion.unit_id == Unit.id)
                .order_by(ProductUnitConversion.product_id, Unit.name.asc())
                .all()
            )

            product_units = {}
            
            for product in products:
                    product_units[str(product["id"])] = [
                    {
                        "id": product["base_unit_id"],
                        "name": "Base unit",
                        "symbol": product["base_unit_symbol"],
                    }
                ]

            for conversion in conversions:
                product_key = str(conversion.product_id)
            
                product_units.setdefault(product_key, [])
            
                if not any(
                    unit["id"] == conversion.unit_id
                    for unit in product_units[product_key]
                ):
                    product_units[product_key].append(
                        {
                            "id": conversion.unit_id,
                            "name": conversion.unit.name,
                            "symbol": conversion.unit.symbol,
                        }
                    )

            if request.method == "GET":
                store_id = request.query_params.get("store_id")
                if store_id:
                    store_id = int(store_id)
                    ledger_service = LedgerService(session = session)
                    inventory = await run_in_threadpool(ledger_service.get_stock_balances, store_id = store_id, sort_order = SortOrder.ALPHABETICAL_ORDER)
                    return await self.templates.TemplateResponse(request, "inventory.html", {"store_is_selected": True, "inventory": inventory, "products": products, "stores": stores, "product_units": product_units})
                else:
                    return await self.templates.TemplateResponse(request, "inventory.html", {"products": products, "stores": stores, "product_units": product_units})

            elif request.method == "POST":
                
                inventory_service = InventoryService(session = session)

                token = request.session.get("token")
                payload = decode_access_token(token)
                if not payload:
                    return await return_template_with_info(message="Unable to access required info from user's auth token. Contact Admin", products=products, stores=stores, product_units=product_units)

                staff_id = payload.get("staff_id")

                if not staff_id:
                    return await return_template_with_info(message="Unable to access staff_id from user's auth token. Contact Admin", products=products, stores=stores, product_units=product_units)

                form = await request.form()
                store_id = int(form.get("store_id"))
                product_id = int(form.get("product_id"))
                quantity = float(form.get("quantity"))
                unit_id = int(form.get("unit_id"))
                remarks = form.get("remarks")
                
                try:
                    quantity = Decimal(str(form.get("quantity")))
                except (InvalidOperation, TypeError, ValueError):
                    raise ValueError("Quantity must be a valid number.")
                
                if not quantity.is_finite():
                    raise ValueError("Quantity must be finite.")

                await run_in_threadpool(inventory_service.submit_stocktake, 
                    recorded_by = staff_id,
                    store_id = store_id,
                    product_id = product_id,
                    target_quantity = Decimal(quantity),
                    target_unit_id = unit_id,
                    remarks = remarks
                )

                return await return_template_with_info(message="Inventory Taking Successful", products=products, stores=stores, product_units=product_units)

        except Exception as err:
            return await return_template_with_info(message=str(err), stores=[], products=[], product_units=[])

        finally:
            session.close()


class StaffAdmin(ModelView, model=Staff):
    name_plural = "Staff"
    column_list = [Staff.first_name, Staff.last_name, Staff.other_names] #columns to show in read/list view
    form_columns = [Staff.username, Staff.password, Staff.first_name, Staff.last_name, Staff.other_names, Staff.role, Staff.other_details] #columns to show in create-form
    form_overrides = dict(password=PasswordField)
    column_searchable_list = [Staff.username, Staff.first_name, Staff.last_name, Staff.role]
    column_sortable_list = [Staff.username, Staff.first_name, Staff.last_name]
    can_delete = False

    form_args = {
        "username": {
            "validators": [
                Regexp(
                    regex=r"^[a-z0-9_\-]+$",
                    message="username should use only lowercase (small letters) without any space between words"
                )
            ],
        }
    }

    async def on_model_change(self, data, model, is_created, request):
        data["password"] = get_password_hash(data["password"])

    def is_accessible(self, request: Request) -> bool:
        return is_admin(request)

    def is_visible(self, request: Request) -> bool:
        return is_admin(request)


class StockMovementAdmin(ModelView, model=StockMovement):
    column_list = [StockMovement.movement_date, StockMovement.product, StockMovement.store, StockMovement.movement_type, StockMovement.quantity_delta, StockMovement.running_balance, StockMovement.recorder, StockMovement.remarks]
    column_filters = [
        ForeignKeyFilter(StockMovement.store_id, Store.name, title="Store"),
        ForeignKeyFilter(StockMovement.product_id, Product.name, title="Product")
    ]
    column_sortable_list = [StockMovement.movement_date, StockMovement.movement_type]
    can_delete = False
    can_create = False
    can_edit = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)


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

            transaction_date = form.get("date")
            if not transaction_date:
                raise ValueError("Receiving date is required.")

            try:
                receiving_date = date.fromisoformat(transaction_date)
            except ValueError:
                raise ValueError("Receiving date is invalid.")

            source_party = (form.get("source_party") or "").strip()
            if not source_party:
                raise ValueError("Source party is required.")

            remarks = (form.get("remarks") or "").strip()

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

            logger.exception("Unexpected error while recording goods receiving")

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


class GoodsReceivedLedgerAdmin(BaseView):
    name = "Goods Received Ledger"

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

    async def _render(
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
            "goods_received_ledger.html",
            {
                "request": request,
                "stores": stores,
                "selected_store": selected_store,
                "documents": documents or [],
                "message": message,
                "message_type": message_type,
            },
        )

    @expose("/goods-received-ledger", methods=["GET"])
    async def goods_received_ledger(self, request: Request):
        session = make_session()

        try:
            stores = (
                session.query(Store)
                .order_by(Store.name.asc())
                .all()
            )

            store_id_value = request.query_params.get("store_id")

            if not store_id_value:
                return await self._render(
                    request,
                    stores=stores,
                )

            try:
                store_id = int(store_id_value)
            except (TypeError, ValueError):
                return await self._render(
                    request,
                    stores=stores,
                    message="The selected store is invalid.",
                    message_type="danger",
                )

            selected_store = (
                session.query(Store)
                .filter(Store.id == store_id)
                .first()
            )

            if not selected_store:
                return await self._render(
                    request,
                    stores=stores,
                    message="The selected store does not exist.",
                    message_type="danger",
                )

            documents = GoodsReceivedRepo.get_for_store(
                session=session,
                store_id=store_id,
            )

            return await self._render(
                request,
                stores=stores,
                selected_store=selected_store,
                documents=documents,
            )

        except Exception:
            session.rollback()

            return await self._render(
                request,
                stores=[],
                message=(
                    "The goods received ledger could not be loaded. "
                    "Please try again."
                ),
                message_type="danger",
            )

        finally:
            session.close()


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

            dispatch_date_value = form.get("date")

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
                form.get("destination_vessel") or ""
            ).strip()

            remarks = (
                form.get("remarks") or ""
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

            logger.exception(
                "Unexpected error while recording dispatch."
            )

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

