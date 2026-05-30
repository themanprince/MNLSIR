from sqlalchemy.orm import sessionmaker, declarative_base, mapped_column
from sqlalchemy import create_engine, ForeignKey, CheckConstraint, Integer, String, Numeric, Enum, Text, Date, DateTime
from datetime import datetime, date
import enum


Base = declarative_base()

class Store(Base):
    __tablename__ = "stores"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String, nullable=False)


class Product(Base):
    __tablename__ = "products"

    id = mapped_column(Integer, primary_key = True)
    name = mapped_column(String, nullable=False)
    sku = mapped_column(String, unique=True)
    base_unit_id = mapped_column(ForeignKey("units.id"), nullable=False)


class Unit(Base):
    __tablename__ = "units"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String, nullable=False)
    symbol = mapped_column(String)


class ProductUnitConversion(Base):
    __tablename__ = "product_unit_conversions"

    id = mapped_column(Integer, primary_key=True)
    product_id = mapped_column(ForeignKey("products.id"), nullable=False)
    unit_id = mapped_column(ForeignKey("units.id"), nullable=False)
    multiplier_to_base = mapped_column(Numeric(12, 4))


class DocumentType(str, enum.Enum):
    GOODS_RECEIVED = "GOODS_RECEIVED"
    DISPATCH = "DISPATCH"
    STOCK_REQUISITION = "STOCK_REQUISITION"
    ISSUE_RECORDS = "ISSUE_RECORDS"

class Document(Base): # e.g. GoodsReceived, Dispatch, Stock-Requisition-Form etc
    __tablename__ = "documents"

    id = mapped_column(Integer, primary_key=True)
    store_id = mapped_column(ForeignKey("stores.id"), nullable=False)
    document_type = mapped_column(Enum(DocumentType), nullable=False)
    reference_no = mapped_column(String)
    date = mapped_column(Date, nullable=False, default=date.today)
    source_party = mapped_column(String)
    destination_party = mapped_column(String)
    remarks = mapped_column(Text)
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentLine(Base):
    __tablename__ = "document_lines"

    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(ForeignKey("documents.id"), nullable=False)
    product_id = mapped_column(ForeignKey("products.id"), nullable=False)
    entered_quantity = mapped_column(Numeric(12, 4))
    entered_unit_id = mapped_column(ForeignKey("units.id"), nullable=False)
    base_quantity = mapped_column(Numeric(12, 4))


class MovementType(str, enum.Enum):
    RECIEVE = "RECIEVE"
    ISSUE = "ISSUE"
    STOCKTAKE = "STOCKTAKE" #e.g. when a store keeper wishes to update digital stockbalance to align with physical stock balance, likely due to unexplainable discrepancies

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = mapped_column(Integer, primary_key=True)
    store_id = mapped_column(ForeignKey("stores.id"))
    movement_date = mapped_column(Date, nullable=False, default=date.today)
    product_id = mapped_column(ForeignKey("products.id"), nullable=False)
    document_line_id = mapped_column(ForeignKey("document_lines.id"))
    movement_type = mapped_column(Enum(MovementType), nullable=False)
    quantity_delta = mapped_column(Numeric(12, 4)) #how much was received / issued in this stock movement e.g. +2pcs biscuit, -10ctns yoghurt
    remarks = mapped_column(String)
    associated_stockmovement_id = mapped_column(Integer, ForeignKey("stock_movements.id"), nullable = True) #in case this stock movement helps explain another (initially inexplainable) adjusted-StockMovement (i.e. rows with movement_type=MovementType.STOCKTAKE), this column serves as a reference to that adjusted-StockMovement
    running_balance = mapped_column(Numeric(12, 4)) #resulting inventory balance (for the corresponding product) after receiving / issuing the quantity_delta in this stock movement
    target_quantity = mapped_column(Numeric(12, 4), nullable = True) #only for rows having movement_type=MovementType.STOCKTAKE... this column's value should override whatever running_balance was there before it

    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            """
                (movement_type = 'RECIEVE' AND quantity_delta > 0) OR
                (movement_type = 'ISSUE' AND quantity_delta < 0) OR
                (movement_type = 'STOCKTAKE' AND quantity_delta = 0)
            """,
            name = "check_movements_delta_sign"
        ),
    )


class StockBalance(Base): # a pseudo-cache for the present inventory qty of a product (cached due to its need to be computed on several cases)
    __tablename__ = "stock_balances"

    store_id = mapped_column(
        ForeignKey("stores.id"),
        primary_key=True
    )
    product_id = mapped_column(
        ForeignKey("products.id"),
        primary_key=True
    )
    quantity = mapped_column(Numeric(12, 4), default=0)


class ActionType(str, enum.Enum):
    IN_PLACE_EDIT = "IN_PLACE_EDIT"
    BALANCE_OVERWRITE_RECONCILE = "BALANCE_OVERWRITE_RECONCILE"
    INITIAL_STOCK_TAKE = "INITIAL_STOCK_TAKE"
    EXPLAIN_DISCREPANCY = "EXPLAIN_DISCREPANCY"

class InterventionLog(Base):
    # this table serves as audit trail for human intervention to stock inventory
    # e.g. someone edits the quantity_delta of a past Stockovement record in place.
    # e.g. someone updates digital StockBalance record to align with physical stock balance records on observation of discrepancies
    __tablename__ = "intervention_logs"

    id = mapped_column(Integer, primary_key = True)
    store_id = mapped_column(Integer, ForeignKey("stores.id"), nullable = False)
    product_id = mapped_column(Integer, ForeignKey("products.id"), nullable = False)
    source_action_type = mapped_column(Enum(ActionType), nullable = False)
    concerned_movement_id = mapped_column(Integer, ForeignKey("stock_movements.id"), nullable = True) #the StockMovement row that this log was created for i.e. the StockMovement row that is edited, adjusted or created
    old_value_snapshot = mapped_column(Numeric(12, 4), nullable = True) #nullable = True because this could be a fresh inventory taking
    new_value_snapshot = mapped_column(Numeric(12, 4), nullable = False)
    changed_by = mapped_column(String)
    remarks = mapped_column(String)
    changed_at = mapped_column(DateTime, default=datetime.utcnow)



engine = create_engine("sqlite:///./db_file.db")

make_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_session():
    session = make_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
