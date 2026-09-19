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
from service.LedgerService import LedgerService, SortOrder
from service.InventoryService import InventoryService
from schema.ReceiveIssueItem import ReceiveIssueItem
from schema.ReceiveIssueStockRequest import ReceiveStockRequest



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

        async def return_template_with_info(message, products, stores):
            return await self.templates.TemplateResponse(request, "inventory.html", {"message": message, "products": products, "stores": stores})

        try:
            products = await run_in_threadpool(ProductRepo(session = session).get_all_products)
            stores = await run_in_threadpool(StoreRepo.get_all_stores, session = session)

            if request.method == "GET":
                store_id = request.query_params.get("store_id")
                if store_id:
                    store_id = int(store_id)
                    ledger_service = LedgerService(session = session)
                    inventory = await run_in_threadpool(ledger_service.get_stock_balances, store_id = store_id, sort_order = SortOrder.ALPHABETICAL_ORDER)
                    return await self.templates.TemplateResponse(request, "inventory.html", {"store_is_selected": True, "inventory": inventory, "products": products, "stores": stores})
                else:
                    return await self.templates.TemplateResponse(request, "inventory.html", {"products": products, "stores": stores})

            elif request.method == "POST":
                
                inventory_service = InventoryService(session = session)

                token = request.session.get("token")
                payload = decode_access_token(token)
                if not payload:
                    return await return_template_with_info(message="Unable to access required info from user's auth token. Contact Admin", products=products, stores=stores)

                staff_id = payload.get("staff_id")

                if not staff_id:
                    return await return_template_with_info(message="Unable to access staff_id from user's auth token. Contact Admin", products=products, stores=stores)

                form = await request.form()
                store_id = int(form.get("store_id"))
                product_id = int(form.get("product_id"))
                quantity = float(form.get("quantity"))
                remarks = form.get("remarks")

                await run_in_threadpool(inventory_service.submit_stocktake, 
                    recorded_by = staff_id,
                    store_id = store_id,
                    product_id = product_id,
                    target_quantity = Decimal(quantity),
                    remarks = remarks
                )

                return await return_template_with_info(message="Inventory Taking Successful", products=products, stores=stores)

        except Exception as err:
            return await return_template_with_info(message=str(err), stores=[], products=[])

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
    name = "Goods Receiving"
    
    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)
    
    @staticmethod
    def _get_form_data(session):
        """
        Load all data required by the goods receiving form.

        Product units are represented as:
        {
            product_id: [
                {
                    "id": unit_id,
                    "name": unit_name,
                    "symbol": unit_symbol,
                }
            ]
        }
        """
        stores = session.query(Store).order_by(Store.name.asc()).all()

        products = (
            session.query(Product)
            .join(Unit, Product.base_unit_id == Unit.id)
            .order_by(Product.name.asc())
            .all()
        )

        units = session.query(Unit).order_by(Unit.name.asc()).all()

        conversions = (
            session.query(ProductUnitConversion)
            .join(Unit, ProductUnitConversion.unit_id == Unit.id)
            .order_by(ProductUnitConversion.product_id, Unit.name.asc())
            .all()
        )

        product_units = {}

        for product in products:
            product_units[str(product.id)] = [
                {
                    "id": product.base_unit.id,
                    "name": product.base_unit.name,
                    "symbol": product.base_unit.symbol,
                }
            ]

        for conversion in conversions:
            product_key = str(conversion.product_id)

            product_units.setdefault(product_key, [])

            # Avoid duplicating the base unit if a conversion rule exists
            # for the product's base unit.
            if not any(
                unit["id"] == conversion.unit_id
                for unit in product_units[product_key]
            ):
                product_units[product_key].append(
                    {
                        "id": conversion.unit.id,
                        "name": conversion.unit.name,
                        "symbol": conversion.unit.symbol,
                    }
                )

        return {
            "stores": stores,
            "products": products,
            "units": units,
            "product_units": product_units,
        }
    
    
    async def _render(
        self,
        request: Request,
        session,
        *,
        message: str | None = None,
        message_type: str = "info",
        form_data: dict | None = None,
    ):
        """
        Render the page while ensuring dropdown values are loaded from
        the current database state.
        """
        context = self._get_form_data(session)

        context.update(
            {
                "request": request,
                "message": message,
                "message_type": message_type,
                "form_data": form_data or {},
                "today": date.today().isoformat(),
            }
        )

        return await self.templates.TemplateResponse(
            request,
            "goods_receiving.html",
            context,
        )
    
    
    @staticmethod
    def _parse_decimal(value: str, field_name: str) -> Decimal:
        value = (value or "").strip()

        if not value:
            raise ValueError(f"{field_name} is required.")

        try:
            quantity = Decimal(value)
        except (InvalidOperation, ValueError):
            raise ValueError(f"{field_name} must be a valid number.")

        if not quantity.is_finite():
            raise ValueError(f"{field_name} must be a finite number.")

        if quantity <= 0:
            raise ValueError(f"{field_name} must be greater than zero.")

        return quantity

    @staticmethod
    def _parse_positive_int(value: str, field_name: str) -> int:
        value = (value or "").strip()

        try:
            parsed = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} is invalid.")

        if parsed <= 0:
            raise ValueError(f"{field_name} is invalid.")

        return parsed

    @staticmethod
    def _get_authenticated_staff_id(request: Request) -> int:
        token = request.session.get("token")
        payload = decode_access_token(token)

        if not payload:
            raise PermissionError(
                "Your session has expired. Please sign in again."
            )

        staff_id = payload.get("staff_id")

        if not staff_id:
            raise PermissionError(
                "Unable to identify the staff member recording this transaction."
            )

        try:
            return int(staff_id)
        except (TypeError, ValueError):
            raise PermissionError(
                "The authenticated staff identity is invalid."
            )

    @expose("/goods-receiving", methods=["GET", "POST"])
    async def goods_receiving(self, request: Request):
        session = make_session()

        try:
            if request.method == "GET":
                return await self._render(request, session)

            staff_id = self._get_authenticated_staff_id(request)
            form = await request.form()

            store_id = self._parse_positive_int(
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

            if receiving_date > date.today():
                raise ValueError(
                    "Receiving date cannot be in the future."
                )

            source_party = (form.get("source_party") or "").strip()
            if not source_party:
                raise ValueError("Source party is required.")

            remarks = (form.get("remarks") or "").strip()

            product_ids = form.getlist("product_id")
            unit_ids = form.getlist("unit_id")
            quantities = form.getlist("quantity")

            if not product_ids:
                raise ValueError(
                    "Add at least one product to the receiving transaction."
                )

            if not (
                len(product_ids)
                == len(unit_ids)
                == len(quantities)
            ):
                raise ValueError(
                    "The receiving line items are incomplete. "
                    "Please review the form and try again."
                )

            items = []

            for index, (product_id_value, unit_id_value, quantity_value) in enumerate(
                zip(product_ids, unit_ids, quantities),
                start=1,
            ):
                product_id = self._parse_positive_int(
                    product_id_value,
                    f"Product on line {index}",
                )

                unit_id = self._parse_positive_int(
                    unit_id_value,
                    f"Unit on line {index}",
                )

                quantity = self._parse_decimal(
                    quantity_value,
                    f"Quantity on line {index}",
                )

                product = session.query(Product).filter_by(id=product_id).first()
                if not product:
                    raise ValueError(
                        f"Product selected on line {index} no longer exists."
                    )

                unit = session.query(Unit).filter_by(id=unit_id).first()
                if not unit:
                    raise ValueError(
                        f"Unit selected on line {index} no longer exists."
                    )

                # A product can be entered in its base unit or in a unit
                # with a configured conversion rule.
                valid_unit_ids = {product.base_unit_id}

                conversion_exists = (
                    session.query(ProductUnitConversion.id)
                    .filter(
                        ProductUnitConversion.product_id == product_id,
                        ProductUnitConversion.unit_id == unit_id,
                    )
                    .first()
                )

                if conversion_exists:
                    valid_unit_ids.add(unit_id)

                if unit_id not in valid_unit_ids:
                    raise ValueError(
                        f"Unit '{unit.name}' is not configured for "
                        f"product '{product.name}' on line {index}."
                    )

                items.append(
                    ReceiveIssueItem(
                        product_id=product_id,
                        unit_id=unit_id,
                        quantity=quantity,
                    )
                )

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