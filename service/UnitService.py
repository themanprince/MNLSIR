from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import ProductUnitConversion, Product, Unit
from exceptions import UnitConversionError, CreateConversionRuleError


class UnitService:

    def __init__(self, session: Session):
        self.session = session
    
    def to_base(self, product_id: int, quantity: Decimal, from_unit_id: int):
        
        product = self.session.query(Product).filter_by(product_id = product_id).first()

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

        return conversion_rule