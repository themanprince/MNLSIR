import pytest
from sqlalchemy.orm import Session
from .conftest import db_session
from .helpers import seed_test_unit, setup_achi, setup_yoghurt_plain
from service.UnitService import UnitService
from exceptions import UnitConversionError
from decimal import Decimal



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
    quantity = Decimal("-2")
    result = unit_service.to_base(product_id = product.id, quantity=quantity, from_unit_id = other_unit.id)

    assert result == -20


def test_convert_to_base_missing_rule_raises_exception(db_session):
    base_unit, other_unit, product, multiplier_to_base = setup_achi(session = db_session)
    no_rule_unit = seed_test_unit(session = db_session, name="unit_x", symbol="ux")

    unit_service = UnitService(session = db_session)
    with pytest.raises(UnitConversionError):
        unit_service.to_base(product_id = product.id, quantity=Decimal("23"), from_unit_id=no_rule_unit.id)