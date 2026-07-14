import pytest

from backend.repo.StoreRepo import StoreRepo
from db import Store
from .conftest import db_session
from exceptions import CreateStoreError


def test_store_repo_create_new_store_works_AND_lowercases_store_name(db_session):
    store_name = "My Store"
    store_details = StoreRepo.create_new_store(store_name=store_name, session=db_session)
    store_id = store_details.store_id
    store = db_session.query(Store).filter_by(id = store_id).first()

    assert store.name == store_name.lower()


def test_store_repo_wont_create_new_store_with_same_name_as_existing(db_session):
    store_name = "random"
    StoreRepo.create_new_store(store_name = store_name, session=db_session)

    with pytest.raises(CreateStoreError):
        StoreRepo.create_new_store(store_name = store_name, session=db_session)