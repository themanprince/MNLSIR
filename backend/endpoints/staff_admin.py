from sqladmin import ModelView
from starlette.requests import Request
from wtforms import PasswordField
from wtforms.validators import Regexp
from db import Staff
from auth import is_admin, get_password_hash




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
