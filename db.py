from sqlalchemy.orm import sessionmaker, declarative_base, mapped_column
from sqlalchemy import create_engine, ForeignKey, Integer, String, Numeric, Enum, Text, Date, DateTime
from datetime import datetime

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = mapped_column(Integer, primary_key = True)
    name = mapped_column(String, nullable=False)
    sku = mapped_column(String, unique=True)
    base_unit_id = mapped_column(ForeignKey("units.id"))


class Unit(Base):
    __tablename__ = "units"

    id = mapped_column(Integer, primary_key=True)
    name = mapped_column(String, nullable=False)
    symbol = mapped_column(String)


class ProductUnitConversion(Base):
    __tablename__ = "product_unit_conversions"

    id = mapped_column(Integer, primary_key=True)
    product_id = mapped_column(ForeignKey("products.id"))
    unit_id = mapped_column(ForeignKey("units.id"))
    multiplier_to_base = mapped_column(Numeric(12, 4))


class DocumentType(str, Enum):
    GOODS_RECEIVED = "GOODS_RECEIVED"
    DISPATCH = "DISPATCH"
    STOCK_REQUISITION = "STOCK_REQUISITION"
    ISSUE_RECORDS = "ISSUE_RECORDS"

class Document(Base): # e.g. GoodsReceived, Dispatch, Stock-Requisition-Form etc
    __tablename__ = "documents"

    id = mapped_column(Integer, primary_key=True)
    document_type = mapped_column(DocumentType, nullable=False)
    reference_no = mapped_column(String)
    date = mapped_column(Date, nullable=False)
    source_party = mapped_column(String)
    destination_party = mapped_column(String)
    remarks = mapped_column(Text)
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DocumentLine(Base):
    __tablename__ = "document_lines"

    id = mapped_column(Integer, primary_key=True)
    document_id = mapped_column(ForeignKey("documents.id"))
    product_id = mapped_column(ForeignKey("products.id"))
    entered_qty = mapped_column(Numeric(12, 4))
    entered_unit_id = mapped_column(ForeignKey("units.id"))
    base_qty = mapped_column(Numeric(12, 4))


class MovementType(str, Enum):
    RECIEVE = "RECEIVE"
    ISSUE = "ISSUE"
    ADJUST = "ADJUST"

class StockMovement(Base):
    __tablename__ = "inventory_movements"

    id = mapped_column(Integer, primary_key=True)
    movement_date = mapped_column(Date, nullable=False)
    product_id = mapped_column(ForeignKey("products.id"))
    document_line_id = mapped_column(ForeignKey("document_lines.id"))
    movement_type = mapped_column(MovementType, nullable=False)
    quantity_delta = mapped_column(Numeric(12, 4)) #how much was received / issued in this stock movement e.g. +2pcs biscuit, -10ctns yoghurt
    running_balance = mapped_column(Numeric(12, 4)) #resulting inventory balance (for the corresponding product) after receiving / issuing the qty in this stock movement
    created_at = mapped_column(DateTime, default=datetime.utcnow)
    updated_at = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockBalance(Base): # a pseudo-cache for the present inventory qty of a product (cached due to its need to be computed on several cases)
    __tablename__ = "stock_balances"

    product_id = mapped_column(
        ForeignKey("products.id"),
        primary_key=True
    )
    quantity = mapped_column(Numeric(12, 4), default=0)



engine = create_engine(f"sqlite:///./db_file.db")
conn = engine.connect()

make_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(engine)

def get_session():
	session = make_session()
	try:
		yield session
	finally:
		session.close()
