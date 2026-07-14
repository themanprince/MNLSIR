from fastapi import APIRouter, HTTPException, Depends, Body
from service.UnitService import UnitService
from db import get_session
from schema.UnitPayload import UnitPayload
from typing import List


UnitRouter = APIRouter(prefix = "/unit")


@UnitRouter.get("/all", response_model=List[UnitPayload])
async def get_all_units(session = Depends(get_session)):
    try:        
        return (UnitService(session = session)).get_all_units()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@UnitRouter.post("/", response_model = UnitPayload, status_code=201)
async def create_unit(session = Depends(get_session), unit_name:str = Body(embed=True), unit_symbol:str = Body(embed=True)):
    try:
       unit_service = UnitService(session = session)
       return unit_service.create_unit(unit_name=unit_name, unit_symbol = unit_symbol)
    except Exception as e:
        raise HTTPException(status_code = 500, detail = str(e))