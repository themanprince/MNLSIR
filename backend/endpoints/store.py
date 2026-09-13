from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from pathlib import Path
from db import get_session
from repo.StoreRepo import StoreRepo
from schema.CreateStoreResponse import CreateStoreResponse


StoreRouter = APIRouter(prefix="/store")

top = Path(__file__).resolve().parent.parent

template_obj = Jinja2Templates(directory=f"{top}/templates")


@StoreRouter.post("/", response_model = CreateStoreResponse, status_code=201)
async def create_store(request:Request, store_name:str = Form(), session = Depends(get_session)):
    try:
        store_details = StoreRepo.create_new_store(store_name = store_name, session = session)
        
        return template_obj.TemplateResponse("store.html", {
            "request": request,
            "show_response": True,
            "is_success": True,
            "store_details": store_details,
            "directive_after_displaying_details": "redirect_to_list"
        })
    except Exception as e:
        return template_obj.TemplateResponse("store.html", {
            "request": request,
            "show_response": True,
            "is_success": False,
            "details": str(e),
            "directive_after_displaying_details": "redirect_to_list"
        })


@StoreRouter.get("/")
async def get_all_stores(request: Request, session = Depends(get_session)):
    try:
        stores = StoreRepo.get_all_stores(session = session)
        return template_obj.TemplateResponse("store.html", {
            "request": request,
            "stores": stores
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
