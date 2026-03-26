from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

TEST_DB = Path(__file__).resolve().parent / 'test_app.db'
os.environ['DATABASE_URL'] = f'sqlite:///{TEST_DB.as_posix()}'
os.environ['LDAP_ENABLED'] = 'false'
os.environ['ALLOW_LOCAL_AUTH'] = 'true'
os.environ['LOCAL_ADMIN_USERNAME'] = 'admin'
os.environ['LOCAL_ADMIN_PASSWORD'] = 'ChangeMe123!'
os.environ['FERNET_KEY'] = 'mrdm8jra4qSEVv2PjYk4Sx4J1SGVINeodIZ6Tn6PvxI='
os.environ['AUTO_CREATE_DB'] = 'true'

from app.main import app
from app.models import Base
from app.core.database import engine, SessionLocal
from app.db.bootstrap import bootstrap_defaults


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        bootstrap_defaults(session)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
