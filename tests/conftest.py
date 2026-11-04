from datetime import date

import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(
        database_url=f"sqlite:///{(tmp_path / 'demo.db').as_posix()}",
        demo_start_date=date(2026, 11, 3),
    )


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings), base_url="http://localhost") as client:
        yield client
