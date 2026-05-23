# STOVK INTERVENTION REFERS TO MANUAL INFLUENCES TO THE AUTOMATIC FLOW OF INVENTORY
# E.G. by doing a stocktake to override the stock balance arrived at by the stock movement flow
# e.g. by editing a stockmovement record, causing a recalculation of the stock movement records
import pytest

from .conftest import db_session
from .helpers import setup_yoghurt_plain, seed_test_stores, seed_dummy_document_line
from service.InventoryService import InventoryService
from service.StockService import StockService
from db import StockMovement, MovementType, InterventionLog, ActionType, StockBalance
from datetime import date
from decimal import Decimal


@pytest.fixture
def inventory_service(db_session):
    return InventoryService(session = db_session)

@pytest.fixture
def stock_service(db_session):
    return StockService(session = db_session)



def test_doing_stocktake_can_serve_as_baseline_when_no_records_exist(db_session, inventory_service):
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]

    quantity = Decimal("100")
    operator_name = "Prince"

    inventory_service.submit_stocktake(
        store_id = store.id, product_id=yoghurt.id, target_quantity = quantity, operator_name = operator_name, remarks = "Opening this product's record with an inventory stock take"
    )

    stock_movement = db_session.query(StockMovement).filter(StockMovement.store_id == store.id, StockMovement.product_id == yoghurt.id).first()
    assert stock_movement is not None
    assert stock_movement.movement_date == MovementType.STOCKTAKE
    assert stock_movement.target_quantity == quantity
    assert stock_movement.running_balance == quantity

    intervention_log = db_session.query(InterventionLog).filter(InterventionLog.store_id == store.id, InterventionLog.product_id == yoghurt.id, InterventionLog.concerned_movement_id == stock_movement.id).first()
    assert intervention_log is not None
    assert intervention_log.changed_by == operator_name
    assert intervention_log.source_action_type == ActionType.INITIAL_STOCK_TAKE
    assert intervention_log.new_value_snapshot == quantity

    stock_balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == yoghurt.id).first()
    assert stock_balance.quantity == quantity


def test_update_historical_stockmovement_recalculates_forward_and_create_log(db_session, stock_service):
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    base_unit, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)

    incorrect_quantity = Decimal("-50")
    correct_quantity = Decimal("-100")

    document_line1 = seed_dummy_document_line(session = db_session, store_id = store.id, product_id = yoghurt.id, unit_id = base_unit.id)
    quantity_delta1, running_balance1 = Decimal("200"), Decimal("200")
    stock_movement1 = StockMovement(store_id = store.id, product_id = yoghurt.id, document_line_id = document_line1.id, movement_type = MovementType.RECIEVE, quantity_delta = quantity_delta1, running_balance = running_balance1)
    
    document_line2 = seed_dummy_document_line(session = db_session, store_id = store.id, product_id = yoghurt.id, unit_id = base_unit.id)
    quantity_delta2 = incorrect_quantity
    running_balance2 = running_balance1 + quantity_delta2
    stock_movement2 = StockMovement(store_id = store.id, product_id = yoghurt.id, document_line_id = document_line2.id, movement_type = MovementType.ISSUE, quantity_delta = quantity_delta2, running_balance = running_balance2)

    document_line3 = seed_dummy_document_line(session = db_session, store_id = store.id, product_id = yoghurt.id, unit_id = base_unit.id)
    quantity_delta3 = Decimal("20")
    running_balance3 = running_balance2 + quantity_delta3
    stock_movement3 = StockMovement(store_id = store.id, product_id = yoghurt.id, document_line_id = document_line3.id, movement_type = MovementType.RECIEVE, quantity_delta = quantity_delta3, running_balance = running_balance3)

    db_session.add_all([stock_movement1, stock_movement2, stock_movement3])
    db_session.commit()

        