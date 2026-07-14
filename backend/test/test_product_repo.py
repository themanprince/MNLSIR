import pytest

from .conftest import db_session
from .helpers import seed_test_unit
from backend.repo.ProductRepo import ProductRepo
from db import ProductUnitConversion, Product
from exceptions import CreateConversionRuleError, CreateProductError
from schema.UnitConversionRule import UnitConversionRule
from decimal import Decimal


@pytest.fixture
def seeded_units(db_session):
    base_unit = seed_test_unit(session = db_session, name = "base", symbol = "bs")
    pack = seed_test_unit(session = db_session, name = "pack", symbol = "pk")
    carton = seed_test_unit(session = db_session, name="carton", symbol = "ctn")

    return base_unit, pack, carton


def test_create_product_with_conversion_works(db_session, seeded_units):
    product_repo = ProductRepo(session = db_session)
    base_unit, pack, carton = seeded_units

    product_name = "Milo 400g"
    sku="milo_400g"
    base_unit_id = base_unit.id
    conversion_rules = [
        UnitConversionRule(unit_id = pack.id, multiplier_to_base = Decimal("12.0000")),
        UnitConversionRule(unit_id = carton.id, multiplier_to_base = Decimal("48.0000"))
    ]

    product = product_repo.create_product(
        product_name = product_name,
        product_sku=sku,
        base_unit_id = base_unit_id,
        conversion_rules = conversion_rules
    )

    assert product["id"] is not None
    assert product["sku"] == sku
    assert product["base_unit_id"] == base_unit.id

    conversion_rules_stored = db_session.query(ProductUnitConversion).filter_by(product_id = product["id"]).all()
    assert len(conversion_rules_stored) == len(conversion_rules)

    carton_conversion_rule = next(rule for rule in conversion_rules_stored if rule.unit_id == carton.id)
    assert carton_conversion_rule.multiplier_to_base == conversion_rules[1].multiplier_to_base


def test_create_product_enforces_atomicity_on_conversion_failure(db_session, seeded_units):
    product_repo = ProductRepo(session = db_session)
    base_unit, pack, carton = seeded_units
    unexisting_unit_id = 999

    product_name = "Milo 400g"
    sku="milo_400g"
    base_unit_id = base_unit.id
    conversion_rules = [
        UnitConversionRule(unit_id = pack.id, multiplier_to_base = Decimal("12.0000")),
        UnitConversionRule(unit_id = unexisting_unit_id, multiplier_to_base = Decimal("48.0000"))
    ]

    with pytest.raises(CreateConversionRuleError):
        product = product_repo.create_product(
            product_name = product_name,
            product_sku=sku,
            base_unit_id = base_unit_id,
            conversion_rules = conversion_rules
        )

    product_in_db = db_session.query(Product).filter_by(sku = sku).first()
    assert product_in_db is None

    conversion_rules_count = db_session.query(ProductUnitConversion).count()
    assert conversion_rules_count == 0


def test_create_product_with_no_conversion_rule_is_allowed(db_session, seeded_units):
    product_repo = ProductRepo(session = db_session)
    base_unit, _, _ = seeded_units

    product_name = "Milo 400g"
    sku="milo_400g"
    base_unit_id = base_unit.id
    conversion_rules = [] #nada, zero, nun', zilch

    product = product_repo.create_product(
        product_name = product_name,
        product_sku=sku,
        base_unit_id = base_unit_id,
        conversion_rules = conversion_rules
    )

    assert product["id"] is not None
    conversion_rules = db_session.query(ProductUnitConversion).filter_by(product_id = product["id"]).all()
    assert len(conversion_rules) == 0


def test_create_product_fails_on_attempt_to_create_product_with_same_name(db_session, seeded_units):
    product_repo = ProductRepo(session = db_session)
    base_unit, _, _ = seeded_units

    product_name = "Milo 400g"

    product = product_repo.create_product(
        product_name = product_name,
        product_sku="milo_400g",
        base_unit_id = base_unit.id,
        conversion_rules = []
    )

    with pytest.raises(CreateProductError):
        product = product_repo.create_product(
            product_name = product_name,
            product_sku="another_sku",
            base_unit_id = base_unit.id,
            conversion_rules = []
        )


def test_create_product_fails_on_attempt_to_create_product_with_same_sku(db_session, seeded_units):
    product_repo = ProductRepo(session = db_session)
    base_unit, _, _ = seeded_units

    product_sku="milo_400g"

    product = product_repo.create_product(
        product_name = "Milo 400g",
        product_sku = product_sku,
        base_unit_id = base_unit.id,
        conversion_rules = []
    )

    with pytest.raises(CreateProductError):
        product = product_repo.create_product(
            product_name = "another product name",
            product_sku=product_sku,
            base_unit_id = base_unit.id,
            conversion_rules = []
        )
