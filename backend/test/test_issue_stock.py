import pytest
from unittest.mock import MagicMock

from service.InventoryService import InventoryService
from .conftest import db_session
from .helpers import seed_test_stores, seed_test_staff, setup_achi, setup_yoghurt_plain
from schema.ReceiveIssueStockRequest import IssueStockRequest
from schema.ReceiveIssueItem import ReceiveIssueItem
from db import StockMovement, MovementType, Document, DocumentLine, DocumentType
from exceptions import ReceiveIssueStockError
from pydantic import ValidationError
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def mock_unit_service(db_session):
    return MagicMock()

@pytest.fixture
def inventory_service(db_session):
    inventory_service = InventoryService(session = db_session)
    return inventory_service


def test_issue_stock_creates_correct_records(db_session, inventory_service):
    
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    staff = seed_test_staff(session = db_session)
    yoghurt_base_unit, yoghurt_other_unit, yoghurt, yoghurt_multiplier_to_base = setup_yoghurt_plain(session = db_session) #yoghurt is the product that will be used for the test

    qty_in_other_unit = Decimal("2")
    qty_in_base_unit = qty_in_other_unit * yoghurt_multiplier_to_base
    date_issued = date.today()

    payload = IssueStockRequest(
        store_id = store.id,
        date = date_issued,
        dest_party = "Prince",
        remarks="Testing things out",
        recorded_by = staff.id,
        items = [
            ReceiveIssueItem(product_id = yoghurt.id, unit_id = yoghurt_other_unit.id, quantity = qty_in_other_unit)
        ]
    )

    doc = inventory_service.receive_issue_stock(payload)
    db_session.commit()

    #document
    assert doc.id is not None
    assert doc.document_type == DocumentType.ISSUE_RECORDS
    assert doc.store_id == store.id
    
    #document lines
    line = db_session.query(DocumentLine).filter_by(document_id = doc.id).first()
    assert line is not None
    assert line.product_id == yoghurt.id
    assert line.entered_quantity == qty_in_other_unit
    assert line.base_quantity == qty_in_base_unit

    #stock movements
    movement = db_session.query(StockMovement).filter_by(document_line_id = line.id).first()
    assert movement is not None
    assert movement.product_id == yoghurt.id
    assert movement.movement_type == MovementType.ISSUE
    assert movement.quantity_delta == -qty_in_base_unit
    assert movement.movement_date == date_issued
    assert movement.recorded_by == staff.id


def test_issue_stock_rejects_future_date(db_session, inventory_service):
    achi_base_unit, achi_other_unit, achi, achi_multiplier_to_base = setup_achi(session = db_session) #in case you don't know, achi is a product.. it is the product that will be used for the test
    future_date = date.today() + timedelta(days=1)
    staff = seed_test_staff(session = db_session)    
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    
    payload = IssueStockRequest(
        store_id = store.id,
        date = future_date,
        dest_party = "me",
        remarks = "because I want to",
        recorded_by = staff.id,
        items = [
            ReceiveIssueItem(product_id = achi.id, unit_id = achi_other_unit.id, quantity = Decimal("2"))
        ]
    )

    with pytest.raises(ReceiveIssueStockError):
        inventory_service.receive_issue_stock(payload)


def test_issue_stock_raises_error_on_invalid_parameters(db_session, inventory_service):
    achi_base_unit, achi_other_unit, achi, achi_multiplier_to_base = setup_achi(session = db_session)
    staff = seed_test_staff(session = db_session)

    with pytest.raises(ValidationError):    
        payload = IssueStockRequest(
            store_id = "random stuff", #type:ignore (INSTEAD OF INT, I'M PASSING STR TYPE ON PURPOSE)
            date = date.today(),
            dest_party = "me",
            remarks = "because I want to",
            recorded_by = staff.id,
            items = [
                ReceiveIssueItem(product_id = achi.id, unit_id = achi_other_unit.id, quantity = Decimal("2"))
            ]
        )

        inventory_service.receive_issue_stock(payload)


def test_issue_stock_raises_error_on_no_product_to_issue(db_session, inventory_service):
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    staff = seed_test_staff(session = db_session)

    payload = IssueStockRequest(
        store_id = store.id,
        date = date.today(),
        dest_party = "me",
        remarks = "because I want to",
        recorded_by = staff.id,
        items = [] #empty product list here
    )

    with pytest.raises(ReceiveIssueStockError):
        inventory_service.receive_issue_stock(payload)


def test_issue_stock_raises_error_on_negative_quantity(db_session, inventory_service):
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    staff = seed_test_staff(session = db_session)
    yoghurt_base_unit, yoghurt_other_unit, yoghurt, yoghurt_multiplier_to_base = setup_yoghurt_plain(session = db_session)

    payload = IssueStockRequest(
        store_id = store.id,
        date = date.today(),
        dest_party = "Prince",
        remarks="Testing things out",
        recorded_by = staff.id,
        items = [
            ReceiveIssueItem(product_id = yoghurt.id, unit_id = yoghurt_other_unit.id, quantity = Decimal("-2"))
        ]
    )

    with pytest.raises(ReceiveIssueStockError):
        inventory_service.receive_issue_stock(payload)


def test_issue_stock_raises_error_on_zero_quantity(db_session, inventory_service):
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    staff = seed_test_staff(session = db_session)
    yoghurt_base_unit, yoghurt_other_unit, yoghurt, yoghurt_multiplier_to_base = setup_yoghurt_plain(session = db_session)

    payload = IssueStockRequest(
        store_id = store.id,
        date = date.today(),
        dest_party = "Prince",
        remarks="Testing things out",
        recorded_by = staff.id,
        items = [
            ReceiveIssueItem(product_id = yoghurt.id, unit_id = yoghurt_other_unit.id, quantity = Decimal("0"))
        ]
    )

    with pytest.raises(ReceiveIssueStockError):
        inventory_service.receive_issue_stock(payload)



def test_issue_stock_atomic_transaction_rollback(db_session, inventory_service, mock_unit_service):
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    staff = seed_test_staff(session = db_session)
    achi_base_unit, achi_other_unit, achi, achi_multiplier_to_base = setup_achi(session = db_session)
    yoghurt_base_unit, yoghurt_other_unit, yoghurt, yoghurt_multiplier_to_base = setup_yoghurt_plain(session = db_session)

    def side_effect(product_id, quantity, from_unit_id):
        if product_id == achi.id:
            raise RuntimeError("Simulation of random database error")
        return quantity
    
    mock_unit_service.to_base.side_effect = side_effect #exception in side_effect should be raised when InventoryService tries to use this mock_unit_service for unit conversion on the specified product
    inventory_service.unit_service = mock_unit_service

    identifying_remarks = "Evaluating Rollback"
    
    payload = IssueStockRequest(
        store_id = store.id,
        date = date.today(),
        dest_party = "Odumeje",
        remarks = identifying_remarks,
        recorded_by = staff.id,
        items = [
            ReceiveIssueItem(product_id=yoghurt.id, unit_id = yoghurt_other_unit.id, quantity = Decimal("2")),
            ReceiveIssueItem(product_id=achi.id, unit_id = achi_other_unit.id, quantity = Decimal("2")),
        ]
    )

    with pytest.raises(RuntimeError): #as is the error expected to be raised by the side effect
        inventory_service.receive_issue_stock(payload)
    
    # even if the first product was received fine, (having no issues)
    # it is expected that the errors caused by the second product will cause a rollback on the entire transaction, thereby undoing even the receiving of the first product
    doc = db_session.query(Document).filter_by(remarks = identifying_remarks).first()
    assert doc is None
    assert db_session.query(DocumentLine).count() == 0
    assert db_session.query(StockMovement).count() == 0