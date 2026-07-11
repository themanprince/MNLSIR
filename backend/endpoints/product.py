from fastapi import APIRouter, HTTPException, Depends, Body
from service.repo.ProductRepo import ProductRepo, SortOrder
from db import get_session
from schema.ProductPayload import ProductPayload
from schema.UnitConversionRule import UnitConversionRule
from typing import List


ProductRouter = APIRouter(prefix = "/product")

products_sort_order_text_mapping = {
    "alpha": SortOrder.ALPHABETICAL_ORDER
}

@ProductRouter.get("/all", response_model=List[ProductPayload])
async def get_all_products(sort:str = "alpha", offset:int = 0, limit:int = 50, session = Depends(get_session)):
    try:
        sort_order = SortOrder.NO_ORDER
        if sort and sort in products_sort_order_text_mapping:
            sort_order = products_sort_order_text_mapping[sort]
        
        return (ProductRepo(session = session)).get_all_products(sort_order = sort_order, offset = offset, limit = limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@ProductRouter.post("/", response_model = ProductPayload, status_code=201)
async def create_product(session = Depends(get_session), product_name:str = Body(embed=True), product_sku:str = Body(embed=True), base_unit_id:int = Body(embed=True), conversion_rules: List[UnitConversionRule] = Body(embed=True)):
    try:
       product_repo = ProductRepo(session = session)
       return product_repo.create_product(product_name=product_name, product_sku = product_sku, base_unit_id = base_unit_id, conversion_rules = conversion_rules)
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))