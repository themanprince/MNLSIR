import pytest
from sqlalchemy.orm import Session
from conftest import db_session
from service.UnitService import UnitService
from db import Product, Unit, ProductUnitConversion
from exceptions import UnitConversionError
from decimal import Decimal


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



def test_convert_to_base_successful(db_session):
    #should correctly convert a standard unit to its base
    base_unit, other_unit, product, multiplier_to_base = setup_yoghurt_plain(session = db_session)   
    unit_service = UnitService(session = db_session)

    quantity = Decimal("3")
    result = unit_service.to_base(product_id = product.id, quantity=quantity, from_unit_id=other_unit.id)

    assert result == quantity * multiplier_to_base


def test_convert_to_base_same_unit(db_session):
    base_unit, other_unit, product, multiplier_to_base = setup_yoghurt_plain(session = db_session)
    unit_service = UnitService(session = db_session)
    quantity = Decimal("10")
    result = unit_service.to_base(product_id = product.id, quantity=quantity, from_unit_id=base_unit.id)

    assert result == quantity


def test_convert_to_base_decimal_precision(db_session):
    base_unit, other_unit, product, multiplier_to_base = setup_achi(session = db_session)
    unit_service = UnitService(session = db_session)
    quantity = Decimal("1.345")
    result = unit_service.to_base(product_id = product.id, quantity=quantity, from_unit_id=other_unit.id)

    assert pytest.approx(result) == quantity * multiplier_to_base


def test_convert_to_base_zero_quantity(db_session):
    base_unit, other_unit, product, multiplier_to_base = setup_achi(session = db_session)
    unit_service = UnitService(session = db_session)
    quantity = Decimal("0")
    result = unit_service.to_base(product_id = product.id, quantity=quantity, from_unit_id=other_unit.id)

    assert result == 0.0


def test_convert_to_base_negative_quantity(db_session):
    base_unit, other_unit, product, multiplier_to_base = setup_yoghurt_plain(session = db_session)
    unit_service = UnitService(session = db_session)
    quantity = Decimal("-20")
    result = unit_service.to_base(product_id = product.id, quantity=quantity, from_unit_id = other_unit.id)

    assert result == -2


def test_convert_to_base_missing_rule_raises_exception(db_session):
    base_unit, other_unit, product, multiplier_to_base = setup_achi(session = db_session)
    no_rule_unit = seed_test_unit(session = db_session, name="unit_x", symbol="ux")

    unit_service = UnitService(session = db_session)
    with pytest.raises(UnitConversionError):
        unit_service.to_base(product_id = product.id, quantity=Decimal("23"), from_unit_id=no_rule_unit.id)