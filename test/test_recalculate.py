import pytest

from .conftest import db_session
from .helpers import setup_yoghurt_plain, seed_test_stores, seed_dummy_document_line
from service.StockService import StockService
from db import StockBalance, StockMovement, MovementType
from decimal import Decimal
from datetime import date, datetime


@pytest.fixture
def stock_service(db_session):
    return StockService(session=db_session)


def test_recalculate_running_balance_accuracy(db_session, stock_service):
    base_unit, other_unit, product, multiplier_to_base = setup_yoghurt_plain(session=db_session)
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    dummy_document_line = seed_dummy_document_line(session=db_session, store_id = store.id, product_id = product.id, unit_id = other_unit.id)

    m1 = StockMovement(store_id = store.id, product_id = product.id, movement_type = MovementType.RECIEVE, quantity_delta=Decimal("100"), movement_date=date(2026, 5, 10), created_at=datetime(2026, 5, 10, 10, 0), document_line_id = dummy_document_line.id)
    m2 = StockMovement(store_id = store.id, product_id = product.id, movement_type = MovementType.ISSUE, quantity_delta=Decimal("-30"), movement_date=date(2026, 5, 12), created_at=datetime(2026, 5, 12, 10, 0), document_line_id = dummy_document_line.id)
    
    db_session.add_all([m1, m2])
    db_session.commit()

    stock_service.recalculate(store_id = store.id, product_id = product.id, from_movement_date=date(2026, 5, 10))

    assert m1.running_balance == Decimal("100")
    assert m2.running_balance == Decimal("70")

    balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == product.id).first()
    assert balance.quantity == Decimal("70")


def test_recalculate_handles_back_dated_inserts(db_session, stock_service):
    base_unit, other_unit, product, multiplier_to_base = setup_yoghurt_plain(session=db_session)
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    dummy_document_line = seed_dummy_document_line(session=db_session, store_id = store.id, product_id = product.id, unit_id = other_unit.id)

    m1 = StockMovement(store_id = store.id, product_id = product.id, movement_type = MovementType.RECIEVE, quantity_delta=Decimal("50"), movement_date=date(2026, 5, 10), created_at=datetime(2026, 5, 10, 12, 0), document_line_id = dummy_document_line.id)
    m3 = StockMovement(store_id = store.id, product_id = product.id, movement_type = MovementType.ISSUE, quantity_delta=Decimal("-20"), movement_date=date(2026, 5, 14), created_at=datetime(2026, 5, 14, 12, 0), document_line_id = dummy_document_line.id)
    
    db_session.add_all([m1, m3])
    db_session.commit()

    stock_service.recalculate(store_id = store.id, product_id = product.id, from_movement_date=date(2026, 5, 10))

    #before I test the backdating, lemme jus repeat the other test here
    assert m1.running_balance == Decimal("50")
    assert m3.running_balance == Decimal("30")

    m2_backdated = StockMovement(store_id = store.id, product_id = product.id, movement_type = MovementType.RECIEVE, quantity_delta = Decimal("100"), movement_date=date(2026, 5, 12), created_at=datetime(2026, 5, 12, 12, 0), document_line_id = dummy_document_line.id)
    db_session.add(m2_backdated)
    db_session.commit()

    stock_service.recalculate(store_id=store.id, product_id = product.id, from_movement_date = date(2026, 5, 10))

    assert m1.running_balance == Decimal("50")
    assert m2_backdated.running_balance == Decimal("150")
    assert m3.running_balance == Decimal("130")

    balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == product.id).first()
    assert balance.quantity == Decimal("130")



def test_recalculate_tie_breaker_sorting_same_day(db_session, stock_service):
    base_unit, other_unit, product, multiplier_to_base = setup_yoghurt_plain(session=db_session)
    [store] = seed_test_stores(session = db_session, no_of_stores = 1)
    dummy_document_line = seed_dummy_document_line(session=db_session, store_id = store.id, product_id = product.id, unit_id = other_unit.id)

    target_day = date(2026, 5, 15)

    entry_first = StockMovement(store_id = store.id, product_id = product.id, movement_type = MovementType.RECIEVE, quantity_delta=Decimal("10"), movement_date=target_day, created_at=datetime(2026, 5, 15, 8, 0), document_line_id = dummy_document_line.id)
    entry_second = StockMovement(store_id = store.id, product_id = product.id, movement_type = MovementType.RECIEVE, quantity_delta=Decimal("3"), movement_date=target_day, created_at=datetime(2026, 5, 15, 12, 0), document_line_id = dummy_document_line.id)

    db_session.add_all([entry_first, entry_second])
    db_session.commit()

    stock_service.recalculate(store_id = store.id, product_id=product.id, from_movement_date = target_day)

    assert entry_first.running_balance == Decimal("10")
    assert entry_second.running_balance == Decimal("13")

    balance = db_session.query(StockBalance).filter(StockBalance.store_id == store.id, StockBalance.product_id == product.id).first()
    assert balance.quantity == Decimal("13")


def test_recalculate_scope_isolation_by_store(db_session, stock_service):
    base_unit, other_unit, product, multiplier_to_base = setup_yoghurt_plain(session=db_session)
    [store1, store2] = seed_test_stores(session = db_session, no_of_stores = 2)
    dummy_document_line = seed_dummy_document_line(session=db_session, store_id = store1.id, product_id = product.id, unit_id = other_unit.id)

    day = date(2026, 5, 15)

    store1_movement = StockMovement(store_id = store1.id, product_id = product.id, quantity_delta = Decimal("15"), movement_type=MovementType.RECIEVE, movement_date = day, created_at = datetime.now(), document_line_id = dummy_document_line.id)
    store2_movement = StockMovement(store_id = store2.id, product_id = product.id, quantity_delta = Decimal("60"), movement_type=MovementType.RECIEVE, movement_date = day, created_at = datetime.now(), document_line_id = dummy_document_line.id)

    db_session.add_all([store1_movement, store2_movement])
    db_session.commit()

    stock_service.recalculate(store_id = store1.id, product_id=product.id, from_movement_date = day)

    assert store1_movement.running_balance == Decimal("15")
    assert store2_movement.running_balance is None