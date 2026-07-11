from contextlib import asynccontextmanager
from fastapi import FastAPI
from db import Base, engine
from endpoints.ledger import LedgerRouter
from endpoints.store import StoreRouter
from endpoints.inventory import InventoryRouter
from endpoints.product import ProductRouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan = lifespan)

app.include_router(LedgerRouter)
app.include_router(StoreRouter)
app.include_router(InventoryRouter)
app.include_router(ProductRouter)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", reload=True)
