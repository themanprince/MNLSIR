from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin
from db import Base, engine, make_session
from endpoints.admin_views import ProductAdmin, UnitAdmin, StoreAdmin, ProductUnitConversionAdmin, InventoryAdmin, StaffAdmin, StockMovementAdmin
from auth import AuthAdmin, create_superuser_staff
import os
from dotenv import load_dotenv


load_dotenv()

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
admin.add_view(StockMovementAdmin)


if __name__ == "__main__":
	import uvicorn
	PORT = int(os.getenv("PORT", 8000))
	uvicorn.run("main:app", port=PORT,reload=True)
