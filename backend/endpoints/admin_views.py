from sqladmin import ModelView, BaseView, expose, Flash
from db import Unit, Product, Store, ProductUnitConversion
from db import make_session
from repo.StoreRepo import StoreRepo
from repo.ProductRepo import ProductRepo
from service.LedgerService import LedgerService, SortOrder


class UnitAdmin(ModelView, model=Unit):
    column_list = [Unit.id, Unit.name, Unit.symbol]
    column_searchable_list = [Unit.name, Unit.symbol]
    column_sortable_list = [Unit.name, Unit.symbol]
    can_delete = False

class ProductAdmin(ModelView, model=Product):
    column_list = [Product.sku, Product.name, Product.base_unit_id]
    column_searchable_list = [Product.sku, Product.name]
    column_sortable_list = [Product.sku, Product.name]
    can_delete = False

class StoreAdmin(ModelView, model=Store):
    column_list = [Store.name]
    can_delete = False

class ProductUnitConversionAdmin(ModelView, model=ProductUnitConversion):
    column_list = [ProductUnitConversion.product_id, ProductUnitConversion.unit_id, ProductUnitConversion.multiplier_to_base]
    can_delete = False


class InventoryAdmin(BaseView):
    name = "Inventory"
    @expose("/inventory", methods=["GET", "POST"])
    async def get_inventory_view(self, request):
        session = make_session()
        try:
            if request.method == "GET":
                products = ProductRepo(session = session).get_all_products()
                stores = StoreRepo.get_all_stores(session = session)

                store_id = request.query_params.get("store_id")
                if store_id:
                    store_id = int(store_id)
                    ledger_service = LedgerService(session = session)
                    inventory = ledger_service.get_stock_balances(store_id = store_id, sort_order = SortOrder.ALPHABETICAL_ORDER)
                    return await self.templates.TemplateResponse(request, "inventory.html", {"store_is_selected": True, "inventory": inventory, "products": products, "stores": stores})
                else:
                    return await self.templates.TemplateResponse(request, "inventory.html", {"products": products, "stores": stores})

            elif request.method == "POST":
                form = await request.form()
                store_id = int(form.get("store_id"))
        finally:
            session.close()