from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — register all models with Base
from app.db import Base, get_db
from app.main import app

_TEST_DATABASE_URL = "sqlite://"

_test_engine = create_engine(
    _TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_test_engine, "connect")
def _enable_fk(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _override_get_db():  # type: ignore[no-untyped-def]
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client() -> TestClient:
    Base.metadata.create_all(bind=_test_engine)
    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c  # type: ignore[misc]
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_test_engine)


@pytest.fixture(autouse=True)
def _stub_azure(request: pytest.FixtureRequest) -> MagicMock:
    """Stub all Azure SDK calls in unit tests.

    Tests marked @pytest.mark.integration bypass this stub and hit real Azure.
    """
    if request.node.get_closest_marker("integration"):
        yield  # type: ignore[misc]
        return

    with (
        patch("app.clients.azure_search.get_index_client") as mock_ic,
        patch("app.clients.azure_search.get_search_client") as mock_sc,
        patch("app.clients.azure_openai.get_openai_client") as mock_oc,
    ):
        mock_ic.return_value = MagicMock()
        mock_sc.return_value = MagicMock()
        mock_oc.return_value = MagicMock()
        yield mock_ic  # type: ignore[misc]
