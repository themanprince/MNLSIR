# STOVK INTERVENTION REFERS TO MANUAL INFLUENCES TO THE AUTOMATIC FLOW OF INVENTORY
# E.G. by doing a stocktake to override the stock balance arrived at by the stock movement flow
# e.g. by editing a stockmovement record, causing a recalculation of the stock movement records
import pytest

from .conftest import db_session
from .helpers import setup_yoghurt_plain, seed_test_staff, seed_test_stores, seed_dummy_document_line
from service.InventoryService import InventoryService
from service.StockService import StockService
from db import StockMovement, MovementType, InterventionLog, ActionType, StockBalance
from schema.ReceiveIssueStockRequest import ReceiveStockRequest
from schema.ReceiveIssueItem import ReceiveIssueItem
from exceptions import UpdateStockMovementError, AssociateStockMovementError
from datetime import date, timedelta
from decimal import Decimal


@pytest.fixture
def stock_service(db_session):
    return StockService(session = db_session)

@pytest.fixture
def inventory_service(db_session, stock_service):
    inventory_service = InventoryService(session = db_session)
    inventory_service.stock_service = stock_service
    return inventory_service



def test_doing_stocktake_can_serve_as_baseline_when_no_records_exist(db_session, inventory_service):
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    staff = seed_test_staff(session = db_session)

    quantity = Decimal("100")

    inventory_service.submit_stocktake(
        store_id = store.id,
        product_id=yoghurt.id,
        target_quantity = quantity,
        remarks = "Opening this product's record with an inventory stock take",
        recorded_by = staff.id
    )

    stock_movement = db_session.query(StockMovement).filter(StockMovement.store_id == store.id, StockMovement.product_id == yoghurt.id).first()
    assert stock_movement is not None
    assert stock_movement.movement_type == MovementType.STOCKTAKE
    assert stock_movement.target_quantity == quantity
    assert stock_movement.running_balance == quantity
    assert stock_movement.recorded_by == staff.id

    intervention_log = db_session.query(InterventionLog).filter(InterventionLog.concerned_movement_id == stock_movement.id, InterventionLog.store_id == store.id, InterventionLog.product_id == yoghurt.id).first()
    assert intervention_log is not None
    assert intervention_log.recorded_by == staff.id
    assert intervention_log.source_action_type == ActionType.INITIAL_STOCK_TAKE
    assert intervention_log.new_value_snapshot == quantity
    assert intervention_log.recorded_by == staff.id

    stock_balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == yoghurt.id).first()
    assert stock_balance.quantity == quantity


def test_update_historical_stockmovement_recalculates_forward_and_creates_log_FOR_POSITIVE_QUANTITY(db_session, stock_service):
    #Here, I'll test editting a stock movement with POSITIVE quantity_delta

    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    base_unit, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    staff = seed_test_staff(session=db_session)

    wrong_quantity = Decimal("50")
    
    document_line1 = seed_dummy_document_line(session = db_session, store_id = store.id, product_id = yoghurt.id, unit_id = base_unit.id)
    quantity_delta1 = wrong_quantity
    stock_movement1 = StockMovement(movement_date = date(2026, 5, 1), movement_type = MovementType.RECIEVE, store_id = store.id, product_id = yoghurt.id, document_line_id = document_line1.id, quantity_delta = quantity_delta1, recorded_by = staff.id)
    
    document_line2 = seed_dummy_document_line(session = db_session, store_id = store.id, product_id = yoghurt.id, unit_id = base_unit.id)
    quantity_delta2 = Decimal("-20")
    stock_movement2 = StockMovement(movement_date = date(2026, 5, 2), movement_type = MovementType.ISSUE, store_id = store.id, product_id = yoghurt.id, document_line_id = document_line2.id, quantity_delta = quantity_delta2, recorded_by = staff.id)

    db_session.add_all([stock_movement1, stock_movement2])
    db_session.commit()
    db_session.refresh(stock_movement1)
    db_session.refresh(stock_movement2)

    stock_service.recalculate(store_id = store.id, product_id = yoghurt.id, from_movement_date = stock_movement1.movement_date)

    #first, lemmee confirm that the correct running_baoance for each StockMovement was correctly set, before I verify that they could be correctly edited
    expected_stock_balance = Decimal("30")
    assert stock_movement2.running_balance == expected_stock_balance
    assert stock_movement1.running_balance == wrong_quantity
    assert stock_movement2.running_balance == stock_movement2.quantity_delta + stock_movement1.running_balance

    correct_quantity = Decimal("100")

    stock_service.update_historical_stockmovement(movement_id = stock_movement1.id, new_quantity_delta=correct_quantity, recorded_by = staff.id, remarks="testing feature of updating historical stockmovement")
    db_session.refresh(stock_movement1)
    db_session.refresh(stock_movement2)

    expected_stock_balance = correct_quantity + stock_movement2.quantity_delta
    assert stock_movement2.running_balance == expected_stock_balance
    assert stock_movement1.running_balance == correct_quantity
    assert stock_movement2.running_balance == stock_movement2.quantity_delta + stock_movement1.running_balance
    
    balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == yoghurt.id).first()
    assert balance.quantity == expected_stock_balance

    log = db_session.query(InterventionLog).filter(InterventionLog.concerned_movement_id == stock_movement1.id, InterventionLog.store_id == store.id, InterventionLog.product_id == yoghurt.id).first()
    assert log is not None
    assert log.source_action_type == ActionType.IN_PLACE_EDIT
    assert log.recorded_by == staff.id
    assert log.old_value_snapshot == wrong_quantity
    assert log.new_value_snapshot == correct_quantity


def test_update_historical_stockmovement_recalculates_forward_and_creates_log_FOR_NEGATIVE_QUANTITY(db_session, stock_service):
    #Here, I'll test editting a stock movement with NEGATIVE quantity_delta

    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    base_unit, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    staff = seed_test_staff(session = db_session)

    wrong_quantity = Decimal("-50")
    
    document_line1 = seed_dummy_document_line(session = db_session, store_id = store.id, product_id = yoghurt.id, unit_id = base_unit.id)
    quantity_delta1 = Decimal("200")
    stock_movement1 = StockMovement(movement_date = date(2026, 5, 1), movement_type = MovementType.RECIEVE, store_id = store.id, product_id = yoghurt.id, document_line_id = document_line1.id, quantity_delta = quantity_delta1, recorded_by = staff.id)
    
    document_line2 = seed_dummy_document_line(session = db_session, store_id = store.id, product_id = yoghurt.id, unit_id = base_unit.id)
    quantity_delta2 = wrong_quantity
    stock_movement2 = StockMovement(movement_date = date(2026, 5, 2), movement_type = MovementType.ISSUE, store_id = store.id, product_id = yoghurt.id, document_line_id = document_line2.id, quantity_delta = quantity_delta2, recorded_by = staff.id)

    document_line3 = seed_dummy_document_line(session = db_session, store_id = store.id, product_id = yoghurt.id, unit_id = base_unit.id)
    quantity_delta3 = Decimal("20")
    stock_movement3 = StockMovement(movement_date = date(2026, 5, 3), movement_type = MovementType.RECIEVE, store_id = store.id, product_id = yoghurt.id, document_line_id = document_line3.id, quantity_delta = quantity_delta3, recorded_by = staff.id)

    db_session.add_all([stock_movement1, stock_movement2, stock_movement3])
    db_session.commit()
    db_session.refresh(stock_movement1)
    db_session.refresh(stock_movement2)
    db_session.refresh(stock_movement3)

    stock_service.recalculate(store_id = store.id, product_id = yoghurt.id, from_movement_date = stock_movement1.movement_date)

    #first, lemmee confirm that the correct running_baoance for each StockMovement was correctly set, before I verify that they could be correctly edited
    expected_stock_balance = Decimal("170")
    assert stock_movement3.running_balance == expected_stock_balance
    assert stock_movement1.running_balance == quantity_delta1
    assert stock_movement2.running_balance == wrong_quantity + stock_movement1.running_balance
    assert stock_movement3.running_balance == stock_movement2.running_balance + quantity_delta3

    correct_quantity = Decimal("-100")

    stock_service.update_historical_stockmovement(movement_id = stock_movement2.id, new_quantity_delta=correct_quantity, recorded_by = staff.id, remarks="testing feature of updating historical stockmovement")
    db_session.refresh(stock_movement1)
    db_session.refresh(stock_movement2)
    db_session.refresh(stock_movement3)

    expected_stock_balance = Decimal("120")
    assert stock_movement3.running_balance == expected_stock_balance
    assert stock_movement1.running_balance == quantity_delta1
    assert stock_movement2.running_balance == correct_quantity + stock_movement1.running_balance
    assert stock_movement3.running_balance == stock_movement2.running_balance + quantity_delta3
    
    balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == yoghurt.id).first()
    assert balance.quantity == expected_stock_balance

    log = db_session.query(InterventionLog).filter(InterventionLog.concerned_movement_id == stock_movement2.id, InterventionLog.store_id == store.id, InterventionLog.product_id == yoghurt.id).first()
    assert log is not None
    assert log.source_action_type == ActionType.IN_PLACE_EDIT
    assert log.recorded_by == staff.id
    assert log.old_value_snapshot == wrong_quantity
    assert log.new_value_snapshot == correct_quantity


def test_insert_and_link_historical_movement_does_not_break_anchor_math(db_session, inventory_service, stock_service):
    # let me try to explain what the method associate_stock_movement_to_stocktake() is for
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    base_unit, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    staff = seed_test_staff(session = db_session)
    
    received_quantity_delta = Decimal("20")
    missing_quantity_delta = Decimal("-2")
    discovered_quantity = received_quantity_delta + missing_quantity_delta

    # so one day I received some of my product
    inventory_service.receive_issue_stock(ReceiveStockRequest(
        store_id = store.id,
        source_party = "Prince",
        remarks="Receiving yoghurt to test (and illustrate) associate_stock_movement_to_stocktake()",
        date = date(2026, 4, 28),
        recorded_by = staff.id,
        items = [
            ReceiveIssueItem(product_id = yoghurt.id, unit_id = base_unit.id, quantity = received_quantity_delta)
        ]
    ))

    # but then, I went to the store one day and discovered that the shelf for yoghurt had 18pcs instead of 20pcs
    # what to do?... I just updated my inventory to reflect the newly discovered quantity
    stock_take = inventory_service.submit_stocktake(target_quantity = discovered_quantity, store_id = store.id, product_id = yoghurt.id, stocktake_date = date.today(), recorded_by = staff.id, remarks = "wetin do our yoghurt.. yhen yhen")

    #this is supposed to make my stockBalance equal to the discvoerd quantity]
    stock_balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == yoghurt.id).first()
    assert stock_balance.quantity == discovered_quantity

    #its also supposed to insert a stock_take record to indicate the discovered quantity on recount
    stock_movement = db_session.query(StockMovement).filter(StockMovement.store_id == store.id, StockMovement.product_id == yoghurt.id, StockMovement.movement_type == MovementType.STOCKTAKE).first()
    assert stock_movement is not None
    assert stock_movement.target_quantity == discovered_quantity

    # but then, as the  story goes, I later discovered one day that sommebody entered the store and, feeling hungry, drank some yoghurts
    # thus, I have to create a stock movement record for this action
    # I also have to indicate that this new stock movement helps to explain the sudden stocktake earlier
    # this is the purpose of insert_and_link_historical_movement()

    explanatory_stock_movement = stock_service.insert_and_link_historical_movement(store_id = store.id, product_id = yoghurt.id, associated_stocktake_id=stock_take.id, movement_type=MovementType.ISSUE, quantity_delta = missing_quantity_delta, movement_date = date(2026, 5, 1), recorded_by = staff.id, remarks = "Somebody was hungry and drank two yoghurts")

    assert explanatory_stock_movement.associated_stockmovement_id == stock_take.id
    assert explanatory_stock_movement.running_balance == discovered_quantity

    db_session.refresh(stock_take)
    assert stock_take.running_balance == discovered_quantity

    #my stock_balance is not supposed to change despite the addition of new stock movement record, as it reflects the physical inventory
    stock_balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == yoghurt.id).first()
    assert stock_balance.quantity == discovered_quantity


def test_delayed_stocktake_submission_corrects_timeline(db_session, inventory_service, stock_service):
    #confirms that backdated stock_takes safely inject themselves as anchors wherever they are inserted
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    staff = seed_test_staff(session = db_session)

    quantity_delta1 = Decimal("100")
    stock_movement1 = StockMovement(store_id = store.id, product_id = yoghurt.id, movement_date = date(2026, 5, 10), movement_type = MovementType.RECIEVE, quantity_delta = quantity_delta1, recorded_by = staff.id)
    db_session.add(stock_movement1)
    db_session.commit()

    quantity_delta2 = Decimal("50")
    stock_movement2 = StockMovement(store_id = store.id, product_id = yoghurt.id, movement_date = date(2026, 5, 18), movement_type = MovementType.RECIEVE, quantity_delta = quantity_delta2, recorded_by = staff.id)
    db_session.add(stock_movement2)
    db_session.commit()

    stock_service.recalculate(store_id = store.id, product_id = yoghurt.id, from_movement_date = stock_movement1.movement_date)

    stock_balance = db_session.query(StockBalance).filter_by(store_id = store.id, product_id = yoghurt.id).first()

    expected_stock_balance_before_stocktake_is_taken = quantity_delta1 + quantity_delta2
    assert stock_movement2.running_balance == expected_stock_balance_before_stocktake_is_taken
    assert stock_balance.quantity == expected_stock_balance_before_stocktake_is_taken

    stocktake_quantity = Decimal("90")
    inventory_service.submit_stocktake(store_id = store.id, product_id = yoghurt.id, stocktake_date = date(2026, 5, 15), target_quantity = stocktake_quantity, recorded_by = staff.id, remarks = "testing delayed submission of stocktake")

    expected_balance_after_stocktake_is_taken = stocktake_quantity + quantity_delta2
    db_session.refresh(stock_movement2)
    assert stock_movement2.running_balance == expected_balance_after_stocktake_is_taken
    db_session.refresh(stock_balance)
    assert stock_balance.quantity == expected_balance_after_stocktake_is_taken


def test_backdated_stockmovement_among_multiple_stocktakes_clamped_by_anchors(db_session, inventory_service, stock_service):
    # ensures a backdated stock_movement updates history up till the point where the next anchor clamps it (by anchor, I mean stock_takes which force the stock balance to conform to a certain value regardless of preceding stock_movements running balances)
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    staff = seed_test_staff(session = db_session)

    stocktake_quantity1 = Decimal("50")
    stock_take1 = inventory_service.submit_stocktake(store_id=store.id, product_id = yoghurt.id, stocktake_date = date(2026, 5, 1), target_quantity = stocktake_quantity1, recorded_by = staff.id, remarks="First Stock Take")
    stocktake_quantity2 = Decimal("100")
    stock_take2 = inventory_service.submit_stocktake(store_id=store.id, product_id = yoghurt.id, stocktake_date = date(2026, 5, 10), target_quantity = stocktake_quantity2, recorded_by = staff.id, remarks="Second Stock Take")

    stock_movement_quantity_delta1 = Decimal("-20")
    mid_stock_movement1 = stock_service.insert_and_link_historical_movement(store_id = store.id, product_id = yoghurt.id, associated_stocktake_id = stock_take2.id, movement_date = date(2026, 5, 6), quantity_delta = stock_movement_quantity_delta1, movement_type=MovementType.ISSUE, recorded_by = staff.id, remarks = "Issuing out product to test program logic")
        
    db_session.refresh(stock_take1)
    db_session.refresh(stock_take2)
    db_session.refresh(mid_stock_movement1)

    assert mid_stock_movement1.running_balance == stocktake_quantity1 + stock_movement_quantity_delta1
    assert stock_take2.running_balance == stocktake_quantity2 #should be unchanged by inserted stock movement
    
    stock_balance = db_session.query(StockBalance).filter_by(store_id = store.id, product_id = yoghurt.id).first()
    assert stock_balance.quantity == stocktake_quantity2

    stock_movement_quantity_delta2 = Decimal("40")
    mid_stock_movement2 = stock_service.insert_and_link_historical_movement(store_id = store.id, product_id = yoghurt.id, associated_stocktake_id = stock_take2.id, movement_date = date(2026, 5, 8), quantity_delta = stock_movement_quantity_delta2, movement_type=MovementType.RECIEVE, recorded_by = staff.id, remarks = "Receiving product to test program logic")

    db_session.refresh(stock_take2)
    db_session.refresh(mid_stock_movement1)
    db_session.refresh(mid_stock_movement2)
    db_session.refresh(stock_balance)

    assert stock_take2.running_balance == stocktake_quantity2 #should be unchanged by inserted stock movement
    assert mid_stock_movement1.running_balance == stocktake_quantity1 + stock_movement_quantity_delta1
    assert mid_stock_movement2.running_balance == stocktake_quantity1 + stock_movement_quantity_delta1 + stock_movement_quantity_delta2
    assert stock_balance.quantity == stocktake_quantity2


def test_historical_update_in_store_1_does_not_leak_or_alter_store_2(db_session, stock_service):
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    [store1, store2] = seed_test_stores(session = db_session, no_of_stores=2)
    staff = seed_test_staff(session = db_session)

    store1_quantity_delta = Decimal("20")
    store1_stock_movement = StockMovement(store_id = store1.id, product_id = yoghurt.id, movement_type = MovementType.RECIEVE, quantity_delta = store1_quantity_delta, running_balance = store1_quantity_delta, recorded_by = staff.id)
    
    store2_quantity_delta = Decimal("100")
    store2_stock_movement = StockMovement(store_id = store2.id, product_id = yoghurt.id, movement_type = MovementType.RECIEVE, quantity_delta = store2_quantity_delta, running_balance = store2_quantity_delta, recorded_by = staff.id)
    
    db_session.add_all([store1_stock_movement, store2_stock_movement])
    db_session.commit()
    db_session.refresh(store1_stock_movement)
    db_session.refresh(store2_stock_movement)


    new_quantity_delta = Decimal("200")
    stock_service.update_historical_stockmovement(movement_id = store1_stock_movement.id, new_quantity_delta=new_quantity_delta, recorded_by = staff.id, remarks = "It was discovered that an initial typo error led to wrong values entered")

    db_session.refresh(store1_stock_movement)
    db_session.refresh(store2_stock_movement)
    assert store1_stock_movement.quantity_delta == new_quantity_delta
    assert store2_stock_movement.quantity_delta == store2_quantity_delta


def test_cold_start_with_negative_values_allowed_on_day_one(db_session, stock_service, inventory_service):
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    staff = seed_test_staff(session = db_session)

    negative_quantity_delta = Decimal("-5")
    stock_movement = inventory_service.submit_stocktake(store_id = store.id, product_id = yoghurt.id, target_quantity = negative_quantity_delta, recorded_by = staff.id, stocktake_date = date(2026, 3, 23), remarks = "Taking an initial stocktake with a negative value")
    
    assert stock_movement.running_balance == negative_quantity_delta
    
    stock_balance = db_session.query(StockBalance).filter_by(store_id = store.id, product_id = yoghurt.id).first()
    assert stock_balance.quantity == negative_quantity_delta


def test_submit_stock_take_with_zero_quantity(db_session, inventory_service, stock_service):
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    staff = seed_test_staff(session = db_session)

    quantity_delta1 = Decimal("50")
    stock_movement1 = StockMovement(store_id = store.id, product_id = yoghurt.id, movement_date = date(2026, 5, 1), quantity_delta = quantity_delta1, movement_type = MovementType.RECIEVE, recorded_by = staff.id)
    quantity_delta2 = Decimal("-20")
    stock_movement2 = StockMovement(store_id = store.id, product_id = yoghurt.id, movement_date = date(2026, 5, 23), quantity_delta = quantity_delta2, movement_type = MovementType.ISSUE, recorded_by = staff.id)
    db_session.add_all([stock_movement1, stock_movement2])
    db_session.commit()

    stock_service.recalculate(store_id = store.id, product_id = yoghurt.id, from_movement_date = stock_movement1.movement_date)
    db_session.refresh(stock_movement1)
    db_session.refresh(stock_movement2)

    inventory_service.submit_stocktake(store_id = store.id, product_id = yoghurt.id, target_quantity = Decimal("0"), recorded_by = staff.id, remarks = "Omo, everything cast")

    stock_balance = db_session.query(StockBalance).filter_by(store_id = store.id, product_id = yoghurt.id).first()
    assert stock_balance.quantity == Decimal("0")
    #just to re-affirm
    assert stock_movement2.running_balance == quantity_delta1 + quantity_delta2 #just to re-affirm


def test_invalid_association_raises_error(db_session, stock_service):
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    staff = seed_test_staff(session = db_session)

    with pytest.raises(UpdateStockMovementError):
        stock_service.update_historical_stockmovement(movement_id = 999, new_quantity_delta = Decimal("45"), remarks = "Testing function with unexistent stock mmovement", recorded_by = staff.id)
    
    stock_movement = StockMovement(store_id = store.id, product_id = yoghurt.id, quantity_delta = Decimal("100"), movement_type = MovementType.RECIEVE, recorded_by = staff.id)
    db_session.add(stock_movement)
    db_session.commit()
    db_session.refresh(stock_movement)

    with pytest.raises(AssociateStockMovementError):
        stock_service.associate_stock_movement_to_stocktake(movement_id = stock_movement.id, stocktake_id = 999, recorded_by = staff.id)
    
    log_count = db_session.query(InterventionLog).count()
    assert log_count == 0


def test_remove_association_from_stock_movement_works_and_does_not_affect_math(db_session, inventory_service, stock_service):
    _, _, yoghurt, _ = setup_yoghurt_plain(session = db_session)
    store = seed_test_stores(session = db_session, no_of_stores=1)[0]
    staff = seed_test_staff(session = db_session)
   
    stock_take = inventory_service.submit_stocktake(store_id = store.id, product_id = yoghurt.id, target_quantity = Decimal("20"), recorded_by = staff.id, remarks = "Just testing the software")
    explanatory_stock_movement = stock_service.insert_and_link_historical_movement(movement_date = (date.today() - timedelta(days=2)), store_id = store.id, product_id = yoghurt.id, associated_stocktake_id=stock_take.id, movement_type = MovementType.RECIEVE, quantity_delta = Decimal("10"), recorded_by = staff.id, remarks="Just testing the software")
    
    assert explanatory_stock_movement.associated_stockmovement_id == stock_take.id
    #inserting a random stockmovement so I can carry out a calculation of running balances... the aim is to check later that unlinking the created association does not mess this caculation up
    stock_movement = StockMovement(movement_date = (date.today() - timedelta(days = 1)), store_id = store.id, product_id = yoghurt.id, movement_type = MovementType.ISSUE, quantity_delta = Decimal("-2"), remarks="Be like them tiff", recorded_by = staff.id)
    db_session.add(stock_movement)
    db_session.commit()
    db_session.refresh(stock_movement)
    stock_service.recalculate(store_id = store.id, product_id = yoghurt.id, from_movement_date = stock_movement.movement_date)

    stock_balance = db_session.query(StockBalance).filter_by(store_id = store.id, product_id = yoghurt.id).first()
    stock_balance_quantity_before_removing_association = stock_balance.quantity

    stock_service.remove_association_from_stock_movement(movement_id = explanatory_stock_movement.id, recorded_by = staff.id)
    
    assert explanatory_stock_movement.associated_stockmovement_id is None

    stock_balance = db_session.query(StockBalance).filter_by(store_id = store.id, product_id = yoghurt.id).first()
    stock_balance_quantity_after_removing_association = stock_balance.quantity

    assert stock_balance_quantity_after_removing_association == stock_balance_quantity_before_removing_association
