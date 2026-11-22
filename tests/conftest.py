from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


@pytest.fixture(autouse=True)
def clean_test_caches():
    from backend.engine.price_guard import clear_market_quotes
    import backend.adapters.stocknow_market_sync as sms
    clear_market_quotes()
    sms._ALL_DSE_SHARES_CACHE.clear()
    sms._ALL_DSE_SHARES_UPDATED_AT = 0.0
    yield
    clear_market_quotes()
    sms._ALL_DSE_SHARES_CACHE.clear()
    sms._ALL_DSE_SHARES_UPDATED_AT = 0.0


@pytest.fixture
def settings(tmp_path):
    return Settings(
        database_url=f"sqlite:///{(tmp_path / 'demo.db').as_posix()}",
        demo_start_date=date(2026, 11, 3),
        operator_username="test_operator",
        operator_password="test_password_123",
        stocknow_live_portfolio_id="164580",
        stocknow_test_portfolio_id="164580_test",
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        yield client


@pytest.fixture
def db(client):
    return client.app.state.database
