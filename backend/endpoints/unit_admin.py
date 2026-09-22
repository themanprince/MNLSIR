from sqladmin import ModelView, expose
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from auth import is_logged_in
from db import Unit



class UnitAdmin(ModelView, model=Unit):
    column_list = [Unit.id, Unit.name, Unit.symbol]
    column_searchable_list = [Unit.name, Unit.symbol]
    column_sortable_list = [Unit.name, Unit.symbol]
    can_delete = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)   
