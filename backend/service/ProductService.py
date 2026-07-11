from sqlalchemy.orm import Session
from service.UnitService import UnitService
from schema.UnitConversionRule import UnitConversionRule
from db import Product, ProductUnitConversion
from enum import Enum


class SortOrder(Enum):  # for selecting the order with which to sort stock balances from DB
    NO_ORDER = "NO_ORDER"
    ALPHABETICAL_ORDER = "ALPHABETICAL_ORDER"

SORT_MECHANISM = {  # mapping of SortOrder selection to sorting mechanism
    SortOrder.ALPHABETICAL_ORDER : Product.name.asc()
}

class ProductService:
    def __init__(self, session: Session):
        self.session = session
        self.unit_service = UnitService(session = session)
    
    def get_all_products(self, sort_order: SortOrder = SortOrder.ALPHABETICAL_ORDER, limit: int = 50, offset:int = 0):
        query = self.session.query(Product)
        if sort_order and (sort_order != SortOrder.NO_ORDER) and (sort_order in SORT_MECHANISM):
            query = query.order_by(SORT_MECHANISM[sort_order])
        query = query.offset(offset).limit(limit)
        all_products = query.all()

        payload_to_return = []

        for product in all_products:
            product_payload = {
                "name": product.name,
                "sku": product.sku,
                "base_unit_id": product.base_unit_id
            }
            conversion_rules = self.session.query(ProductUnitConversion).filter_by(product_id = product.id).all()
            product_payload["unit_conversions"] = [{"unit_id": conv.unit_id, "multiplier_to_base": conv.multiplier_to_base} for conv in conversion_rules]
            payload_to_return.append(product_payload)
        
        return payload_to_return

    
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
        
