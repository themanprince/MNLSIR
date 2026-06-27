import pytest

from .conftest import db_session
from .helpers import seed_test_staff, seed_test_stores, seed_test_product, seed_test_unit
from service.InventoryService import InventoryService
from schema.ReceiveIssueStockRequest import ReceiveStockRequest, IssueStockRequest
from schema.ReceiveIssueItem import ReceiveIssueItem
from service.LedgerService import LedgerService, SortOrder
from random import random
from datetime import date
from decimal import Decimal


@pytest.fixture
def inventory_service(db_session):
    return InventoryService(session = db_session)


@pytest.fixture
def ledger_service(db_session):
    return LedgerService(session = db_session)


@pytest.fixture
def store_and_unit_and_staff(db_session):
    store = seed_test_stores(session=db_session, no_of_stores=1)[0]
    unit = seed_test_unit(session = db_session, name="TestUnit", symbol = "TU")
    staff = seed_test_staff(session = db_session)

    return store, unit, staff


@pytest.fixture
def products(db_session, inventory_service, store_and_unit_and_staff):
    products_to_create = [
        #FORMAT IS -> product_name, sku, quantity, ID (to be gotten after insertion to DB)
        ["Boneless", "boneless", 23.5, -1],
        ["Mineral Water", "mineral_water", 200, -1],
        ["Garri (Yellow)", "garri_yellow", 45.3, -1],
        ["Garri (White)", "garri_white", 22, -1],
        ["Digestive (McVities)", "digestive_mcvities", 23, -1],
        ["Crackers Biscuit (Jacobs)", "crackers_biscuit_jacobs", 45, -1],
        ["Indomie", "indomie", 459, -1],
        ["Tomato Ketchup", "tomato_ketchup", 54, -1],
        ["Tomato Paste", "tomato_paste", 63, -1],
        ["Serviette", "serviette", 23, -1]
    ]

    store, unit, staff = store_and_unit_and_staff

    for product_payload in products_to_create:
        product = seed_test_product(session = db_session, name = product_payload[0], sku = product_payload[1], base_unit_id=unit.id) #for testing purposes, they'll all use same base unit
        product_payload[3] = product.id

        inventory_service.submit_stocktake(recorded_by = staff.id, store_id = store.id, product_id = product.id, target_quantity=product_payload[2], remarks = f"Taking stock for {product_payload[0]} for testing purposes")
    
    return products_to_create



def test_get_stock_balances_returns_correct_records_in_alphabetical_order_by_default(ledger_service, products, store_and_unit_and_staff):

    store, unit, staff = store_and_unit_and_staff

    stock_balances = ledger_service.get_stock_balances(store_id=store.id)

    expected_order = sorted(products, key=lambda product_payload:product_payload[0], reverse = False)

    for i in range(len(stock_balances)):
        assert stock_balances[i][0] == expected_order[i][3] #product_id
        assert stock_balances[i][1] == expected_order[i][0] #product_name
        assert pytest.approx(stock_balances[i][2]) == pytest.approx(Decimal(expected_order[i][2])) #expected quantity
    
