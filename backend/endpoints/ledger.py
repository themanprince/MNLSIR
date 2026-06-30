from fastapi import APIRouter

LedgerRouter  = APIRouter(prefix="/ledger")

@LedgerRouter.get("/health")
async def health():
    return 200, "got here"