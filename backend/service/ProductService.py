from sqlalchemy.orm import Session
from service.UnitService import UnitService
from schema.UnitConversionRule import UnitConversionRule
from db import Product


class ProductService:
    def __init__(self, session: Session):
        self.session = session
        self.unit_service = UnitService(session = session)
    
    def create_product(self, product_name: str, product_sku: str, base_unit_id: int, conversions: list[UnitConversionRule]):
        transaction_context = ( # if a transaction is already started, use a nested savepoint transaction. Otherwise, start a top-level transaction
            self.session.begin_nested()
            if self.session.in_transaction()
            else self.session.begin()
        )
        with transaction_context:
            product = Product(name = product_name, sku = product_sku, base_unit_id = base_unit_id)
            self.session.add(product)
            self.session.flush()
            self.session.refresh(product)
            for conversion_rule in conversions:
                self.unit_service.create_conversion_rule(product_id = product.id, unit_id = conversion_rule.unit_id, multiplier_to_base = conversion_rule.multiplier_to_base)
            
            return product