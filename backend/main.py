from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from db import Base, engine
from endpoints.admin_views import ProductAdmin, UnitAdmin, StoreAdmin, ProductUnitConversionAdmin, InventoryAdmin
from auth import AuthAdmin
from endpoints.auth_admin_views import StaffAdmin
from endpoints.ledger import LedgerRouter
from endpoints.store import StoreRouter
from endpoints.inventory import InventoryRouter
from endpoints.product import ProductRouter
from endpoints.unit import UnitRouter
from CONSTANTS import FRONTEND_URL
import os
from dotenv import load_dotenv


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


secret_key = os.getenv("SECRET_KEY2", "")
authentication_backend = AuthAdmin(secret_key = secret_key)

app = FastAPI(lifespan = lifespan)
admin = Admin(app, engine=engine, authentication_backend=authentication_backend)

app.add_middleware(
      CORSMiddleware,
      allow_origins=[FRONTEND_URL],
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

      
app.include_router(LedgerRouter)
app.include_router(StoreRouter)
app.include_router(InventoryRouter)
app.include_router(ProductRouter)
app.include_router(UnitRouter)

if __name__ == "__main__":
	import uvicorn
	PORT = int(os.getenv("PORT", 8000))
	uvicorn.run("main:app", port=PORT,reload=True)
