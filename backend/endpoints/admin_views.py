from sqladmin import ModelView, BaseView, expose, Flash
from db import Unit, Product, Store, ProductUnitConversion
from db import make_session
from repo.StoreRepo import StoreRepo

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


class DeleteThisAdmin(BaseView):
    name = "Delete This"

    @expose("/delete-this", methods=["GET", "POST"])
    async def delete_this(self, request):
        session = make_session()
        if request.method == "GET":
            stores = StoreRepo.get_all_stores(session = session)
            return await self.templates.TemplateResponse(request, "delete-this.html", {"stores": stores})
        elif request.method == "POST":
            form = await request.form()
            store_id = int(form.get("store_id"))
            return await self.templates.TemplateResponse(request, "delete-this.html", {"message": f"Store with id ({store_id}) seen successfully."})
