from contextlib import asynccontextmanager
from fastapi import FastAPI
from db import Base, engine
from endpoints.ledger import LedgerRouter

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan = lifespan)

app.include_router(LedgerRouter)

if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", reload=True)
