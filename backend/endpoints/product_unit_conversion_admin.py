from sqladmin import ModelView
from starlette.requests import Request
from db import ProductUnitConversion
from auth import is_logged_in


class ProductUnitConversionAdmin(ModelView, model=ProductUnitConversion):
    column_list = [ProductUnitConversion.product, ProductUnitConversion.unit, ProductUnitConversion.multiplier_to_base]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)
