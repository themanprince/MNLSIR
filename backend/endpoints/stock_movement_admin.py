from sqladmin import ModelView
from sqladmin.filters import ForeignKeyFilter
from starlette.requests import Request
from db import Product, Store, StockMovement
from auth import is_logged_in



class StockMovementAdmin(ModelView, model=StockMovement):
    name = "Stock Movements"
    name_plural = "Stock Movements"

    column_list = [StockMovement.movement_date, StockMovement.store, StockMovement.source_party, StockMovement.destination_party, StockMovement.product, StockMovement.movement_type, StockMovement.quantity_delta, StockMovement.running_balance, StockMovement.recorder, StockMovement.remarks]

    column_labels = {
        StockMovement.movement_date: "Date",
        StockMovement.product: "Product",
        StockMovement.store: "Store",
        StockMovement.movement_type: "Type",
        StockMovement.source_party: "Source",
        StockMovement.destination_party: "Destination",
        StockMovement.quantity_delta: "Quantity Change",
        StockMovement.running_balance: "Balance",
        StockMovement.recorder: "Recorded By",
        StockMovement.remarks: "Remarks",
    }

    column_filters = [
        ForeignKeyFilter(StockMovement.store_id, Store.name, title="Store"),
        ForeignKeyFilter(StockMovement.product_id, Product.name, title="Product")
    ]
    column_sortable_list = [StockMovement.movement_date, StockMovement.movement_type]

    column_searchable_list = [
        StockMovement.remarks,
    ]

    can_delete = False
    can_create = False
    can_edit = False

    def is_accessible(self, request: Request) -> bool:
        return is_logged_in(request)

    def is_visible(self, request: Request) -> bool:
        return is_logged_in(request)

