from sqlalchemy.orm import Session
from db import Store
from exceptions import CreateStoreError


class StoreRepo:
    @classmethod
    def create_new_store(cls, session:Session, store_name: str):
        existing_store_with_same_name = session.query(Store).filter_by(name = store_name.lower())
        if existing_store_with_same_name:
            raise CreateStoreError(f"Store already exists having name={store_name}")
        
        store_name = store_name.lower()
        store = Store(name = store_name)
        session.add(store)
        session.commit()
        session.refresh(store)
        return store