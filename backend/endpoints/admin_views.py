from sqladmin import ModelView, BaseView, expose
from starlette.requests import Request
from wtforms import PasswordField
from wtforms.validators import Regexp
from decimal import Decimal
from db import Unit, Product, Store, ProductUnitConversion, Staff, StockMovement
from db import make_session
from auth import is_logged_in, get_password_hash, decode_access_token
from repo.StoreRepo import StoreRepo
from repo.ProductRepo import ProductRepo
from service.LedgerService import LedgerService, SortOrder
from service.InventoryService import InventoryService



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
    column_list = [Product.sku, Product.name, Product.base_unit_id]
    column_searchable_list = [Product.sku, Product.name]
    column_sortable_list = [Product.sku, Product.name]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)


class StoreAdmin(ModelView, model=Store):
    column_list = [Store.name]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)


class ProductUnitConversionAdmin(ModelView, model=ProductUnitConversion):
    column_list = [ProductUnitConversion.product_id, ProductUnitConversion.unit_id, ProductUnitConversion.multiplier_to_base]
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
        try:
            products = ProductRepo(session = session).get_all_products()
            stores = StoreRepo.get_all_stores(session = session)

            if request.method == "GET":
                store_id = request.query_params.get("store_id")
                if store_id:
                    store_id = int(store_id)
                    ledger_service = LedgerService(session = session)
                    inventory = ledger_service.get_stock_balances(store_id = store_id, sort_order = SortOrder.ALPHABETICAL_ORDER)
                    return await self.templates.TemplateResponse(request, "inventory.html", {"store_is_selected": True, "inventory": inventory, "products": products, "stores": stores})
                else:
                    return await self.templates.TemplateResponse(request, "inventory.html", {"products": products, "stores": stores})

            elif request.method == "POST":
                async def return_template_with_info(info):
                    return await self.templates.TemplateResponse(request, "inventory.html", {"message": info, "products": products, "stores": stores})

                inventory_service = InventoryService(session = session)

                token = request.session.get("token")
                payload = decode_access_token(token)
                if not payload:
                    return await return_template_with_info("Unable to access required info from user's auth token. Contact Admin")

                staff_id = payload.get("staff_id")

                if not staff_id:
                    return await return_template_with_info("Unable to access staff_id from user's auth token. Contact Admin")

                form = await request.form()
                store_id = int(form.get("store_id"))
                product_id = int(form.get("product_id"))
                quantity = float(form.get("quantity"))
                remarks = form.get("remarks")

                inventory_service.submit_stocktake(
                    recorded_by = staff_id,
                    store_id = store_id,
                    product_id = product_id,
                    target_quantity = Decimal(quantity),
                    remarks = remarks
                )

                return await return_template_with_info("Inventory Taking Successful")

        finally:
            session.close()

            
class StaffAdmin(ModelView, model=Staff):
    column_list = [Staff.id, Staff.username, Staff.first_name, Staff.last_name, Staff.other_names] #columns to show in read/list view
    form_columns = [Staff.username, Staff.password, Staff.first_name, Staff.last_name, Staff.other_names, Staff.other_details] #columns to show in create-form
    form_overrides = dict(password=PasswordField)
    column_searchable_list = [Staff.username, Staff.first_name, Staff.last_name]
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
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)


class StockMovementAdmin(ModelView, model=Product):
    column_list = [StockMovement.movement_date, StockMovement.product_id, StockMovement.store_id, StockMovement.movement_type, StockMovement.quantity_delta, StockMovement.running_balance, StockMovement.recorded_by, StockMovement.remarks]
    column_sortable_list = [StockMovement.movement_date, StockMovement.movement_type]
    can_delete = False
    can_create = False
    can_edit = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)
