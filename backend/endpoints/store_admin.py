from sqladmin import ModelView
from starlette.requests import Request
from db import Store
from auth import is_logged_in



class StoreAdmin(ModelView, model=Store):
    column_list = [Store.name]
    form_columns = [Store.name]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

