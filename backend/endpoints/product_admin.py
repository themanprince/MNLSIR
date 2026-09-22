from sqladmin import ModelView
from starlette.requests import Request
from db import Product
from auth import is_logged_in



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
