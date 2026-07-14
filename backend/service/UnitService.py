from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import ProductUnitConversion, Product, Unit
from exceptions import CreateUnitError, UnitConversionError, CreateConversionRuleError


class UnitService:

    def __init__(self, session: Session):
        self.session = session


    def create_unit(self, unit_name: str, unit_symbol: str):
        unit_name = unit_name.lower()
        unit_symbol = unit_symbol.lower()

        existing_unit_with_same_name = self.session.query(Unit).filter_by(name = unit_name).first()
        existing_unit_with_same_symbol = self.session.query(Unit).filter_by(symbol = unit_symbol).first()

        if existing_unit_with_same_name:
            raise CreateUnitError(f"Unit already exists having name={unit_name}")
        if existing_unit_with_same_symbol:
            raise CreateUnitError(f"Unit already exists having symbol={unit_symbol}")
        
        unit = Unit(name = unit_name, symbol = unit_symbol)
        self.session.add(unit)
        self.session.commit()
        self.session.refresh(unit)
        
        return {
            "unit_id": unit.id,
            "unit_name": unit.name,
            "unit_symbol": unit.symbol
        }


    def get_all_units(self):
        all_units = self.session.query(Unit).order_by(Unit.asc()).all()
        return [
            {"unit_id": unit.id, "unit_name": unit.name, "unit_symbol": unit.symbol}
            for unit in all_units
        ]


    def to_base(self, product_id: int, quantity: Decimal, from_unit_id: int):
        
        product = self.session.query(Product).filter_by(id = product_id).first()

        if not product:
            raise UnitConversionError(f"No product with id={product_id}")

        if from_unit_id == product.base_unit_id:
            return quantity
        
        statement = select(ProductUnitConversion).where(
                ProductUnitConversion.product_id == product_id,
                ProductUnitConversion.unit_id == from_unit_id
            )

        conversion = self.session.execute(statement).scalar_one_or_none()

        if not conversion:
            raise UnitConversionError(f"No conversion rule for product with id={product_id} from unit with id={from_unit_id}")
        
        base_quantity = quantity * Decimal(conversion.multiplier_to_base)

        return base_quantity
    

    def create_conversion_rule(self, product_id:int, unit_id:int, multiplier_to_base:Decimal, override_existing_rule = False):
        existing_rule = self.session.query(ProductUnitConversion).filter(ProductUnitConversion.product_id == product_id, ProductUnitConversion.unit_id == unit_id).first()

        if existing_rule and (not override_existing_rule):
            raise CreateConversionRuleError(f"Conversion rule already exists with product_id={product_id}, unit_id={unit_id}. Try setting override_existing_rule param to True if you wish to override an existing rule")
        
        product = self.session.query(Product).filter(Product.id == product_id).first()
        unit = self.session.query(Unit).filter(Unit.id == unit_id).first()

        if (not product) or (not unit):
            raise CreateConversionRuleError(f"Either of these doesn't exist: Product with id={product_id}, unit with id={unit_id}")
        
        conversion_rule = ProductUnitConversion(
            product_id = product_id,
            unit_id = unit_id,
            multiplier_to_base = multiplier_to_base
        )

        self.session.add(conversion_rule)
        self.session.flush()
        self.session.refresh(conversion_rule)

        return conversion_rule