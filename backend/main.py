from dotenv import load_dotenv

load_dotenv()


from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from sqladmin import Admin
from db import Base, engine, make_session
from endpoints.product_admin import ProductAdmin
from endpoints.unit_admin import UnitAdmin
from endpoints.store_admin import StoreAdmin
from endpoints.product_unit_conversion_admin import ProductUnitConversionAdmin
from endpoints.inventory_admin import InventoryAdmin
from endpoints.staff_admin import StaffAdmin
from endpoints.stock_movement_review_admin import StockMovementReviewAdmin
from endpoints.goods_receiving_admin import GoodsReceivingAdmin
from endpoints.goods_received_ledger_admin import GoodsReceivedLedgerAdmin
from endpoints.issue_stock_admin import IssueStockAdmin
from endpoints.dispatch_admin import DispatchAdmin
from endpoints.dispatch_ledger_admin import DispatchLedgerAdmin
from auth import AuthAdmin, create_superuser_staff
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    session = make_session()
    try:
        create_superuser_staff(session = session)
    finally:
          session.close()

    yield


secret_key = os.getenv("SECRET_KEY2", "")
authentication_backend = AuthAdmin(secret_key = secret_key)

app = FastAPI(lifespan = lifespan)
admin = Admin(app, engine=engine, authentication_backend=authentication_backend)


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/admin/") #since all the functionality is in admin anyways


app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_methods=["*"],
      allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="templates/static"), name="static")


admin.add_view(StoreAdmin)
admin.add_view(UnitAdmin)
admin.add_view(ProductAdmin)
admin.add_view(ProductUnitConversionAdmin)
admin.add_view(InventoryAdmin)
admin.add_view(StaffAdmin)
admin.add_view(GoodsReceivingAdmin)
admin.add_view(GoodsReceivedLedgerAdmin)
admin.add_view(IssueStockAdmin)
admin.add_view(DispatchAdmin)
admin.add_view(DispatchLedgerAdmin)
admin.add_view(StockMovementReviewAdmin)


if __name__ == "__main__":
	import uvicorn
	PORT = int(os.getenv("PORT", 8000))
	uvicorn.run("main:app", host="0.0.0.0", port=PORT,reload=False)
