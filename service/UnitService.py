from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from db import ProductUnitConversion


class UnitConversionError(Exception):
    pass


class UnitService:

    def __init__(self, session: Session):
        self.session = session
    
    def to_base(self, product_id: int, quantity: Decimal, from_unit_id: int):
        
        if quantity <= 0:
            raise UnitConversionError("Quantity must be positive")
        
        statement = select(ProductUnitConversion).where(
                ProductUnitConversion.product_id == product_id,
                ProductUnitConversion.unit_id == from_unit_id
            )

        conversion = self.session.execute(statement).scalar_one_or_none()

        if not conversion:
            raise UnitConversionError(f"No conversion rule for product with id={product_id} from unit with id={from_unit_id}")
        
        base_quantity = quantity * Decimal(conversion.multiplier_to_base)

        return base_quantity