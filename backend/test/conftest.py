import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Base

TEST_DB_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
get_testing_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    #create tables before test
    Base.metadata.create_all(bind=engine)
    session = get_testing_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
        #drop tables after test to keep clean
        Base.metadata.drop_all(bind=engine)