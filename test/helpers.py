from sqlalchemy.orm import Session
from decimal import Decimal
from db import Unit, Product, ProductUnitConversion


def seed_test_unit(session: Session, name:str, symbol:str):
    unit = Unit(name = name, symbol = symbol)
    session.add(unit)
    session.commit()
    session.refresh(unit)
    return unit


def seed_test_product(session:Session, name:str, sku:str, base_unit_id:int):
    product = Product(name=name, sku=sku, base_unit_id=base_unit_id)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

def seed_conversion_rule(session: Session, product_id: int, unit_id:int, multiplier_to_base: Decimal):
    rule = ProductUnitConversion(
        product_id = product_id,
        unit_id = unit_id,
        multiplier_to_base = multiplier_to_base
    )
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


#next, I'll be putting functions for easily setting up test products, units and conversion rules
def setup_yoghurt_plain(session: Session):
    base_unit = seed_test_unit(session = session, name="piece", symbol="pcs")
    other_unit = seed_test_unit(session = session, name="carton", symbol="ctn")
    product = seed_test_product(session = session, name="Yoghurt Plain", sku="yoghurt-plain", base_unit_id=base_unit.id)
    
    multiplier_to_base = Decimal("10")
    seed_conversion_rule(session = session, product_id = product.id, unit_id=other_unit.id, multiplier_to_base=multiplier_to_base)

    return base_unit, other_unit, product, multiplier_to_base

def setup_achi(session: Session):
    base_unit = seed_test_unit(session = session, name="kilogram", symbol="kg")
    other_unit = seed_test_unit(session = session, name="basket", symbol="bskt")
    product = seed_test_product(session = session, name="Achi", sku="achi", base_unit_id=base_unit.id)
    
    multiplier_to_base = Decimal("2.5")
    seed_conversion_rule(session = session, product_id = product.id, unit_id=other_unit.id, multiplier_to_base=multiplier_to_base)

    return base_unit, other_unit, product, multiplier_to_base
