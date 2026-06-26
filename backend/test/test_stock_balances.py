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
    unit = seed_test_unit(session = db_session, name="TestUnit", symbol = "TU") #for testing purposes, they'll all use same base unit
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
        product = seed_test_product(session = db_session, name = product_payload[0], sku = product_payload[1], base_unit_id=unit.id)
        product_payload[3] = product.id

        inventory_service.submit_stocktake(recorded_by = staff.id, store_id = store.id, product_id = product.id, target_quantity=product_payload[2], remarks = f"Taking stock for {product_payload[0]} for testing purposes")
    
    return products



def test_get_stock_balances_returns_correct_records_in_alphabetical_order_default(db_session, ledger_service, products, store_and_unit_and_staff):

    store, unit, staff = store_and_unit_and_staff

    stock_balances = ledger_service.get_stock_balances(store_id=store.id)

    expected_order = sorted(products, key=lambda product_payload:product_payload[0].lower(), reverse = False)

    for i in range(stock_balances):
        assert stock_balances[i][0] == expected_order[i][3] #product_id
        assert stock_balances[i][1] == expected_order[i][0] #product_name
        assert stock_balances[i][2] == expected_order[i][2] #expected quantity
    

def test_get_stock_balances_still_works_correctly_after_mutations(db_session, ledger_service, inventory_service, products, store_and_unit_and_staff):
    random_product_index1 = round(random() * len(products))
    product1 = products[random_product_index1]
    product1_old_qty = product1[2]
    qty_to_mutate_product1_with = Decimal("10")
    expected_product1_new_qty = product1_old_qty + qty_to_mutate_product1_with

    random_product_index2 = round(random() * len(products))
    product2 = products[random_product_index2]
    product2_old_qty = product2[2]
    qty_to_mutate_product2_with = Decimal("13")
    expected_product2_new_qty = product2_old_qty - qty_to_mutate_product2_with


    store, unit, staff = store_and_unit_and_staff
    
    inventory_service.receive_issue_stock(ReceiveStockRequest(
        store_id = store.id, recorded_by = staff.id, source_party = "Mr. David", date = date.today(), remarks = "Testing something",
        items = [ReceiveIssueItem(product_id = product1.id, unit_id = unit.id, quantity = qty_to_mutate_product1_with)]
    ))

    inventory_service.receive_issue_stock(IssueStockRequest(
        store_id = store.id, recorded_by = staff.id, dest_party = "Me", date = date.today(), remarks = "Testing something",
        items = [ReceiveIssueItem(product_id = product2.id, unit_id = unit.id, quantity = qty_to_mutate_product2_with)]
    ))

    stock_balances = ledger_service.get_stock_balances(store_id=store.id)

    sorted_order = sorted(products, key=lambda product_payload:product_payload[0].lower(), reverse = False)

    for i in range(stock_balances):
        assert stock_balances[i][0] == sorted_order[i][3] #product_id
        assert stock_balances[i][1] == sorted_order[i][0] #product_name
        
        if sorted_order[i] == product1:
            assert stock_balances[i][2] == expected_product1_new_qty
            continue
        elif sorted_order[1] == product2:
            assert stock_balances[i][2] == expected_product2_new_qty
            continue

        assert stock_balances[i][2] == sorted_order[i][2] #expected quantity