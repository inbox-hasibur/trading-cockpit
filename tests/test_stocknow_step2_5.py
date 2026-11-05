import asyncio
from datetime import date, datetime
from fastapi.testclient import TestClient

from backend.config import DHAKA, Settings
from backend.database import Database
from backend.seed import seed_demo
from backend.engine.scheduler import DSEMarketScheduler, is_dse_market_open
from backend.main import create_app


def test_is_dse_market_open_telemetry():
    cfg = Settings()
    # Sunday (weekday=6) at 11:00 AM -> Open
    sun_open = datetime(2026, 11, 8, 11, 0, 0, tzinfo=DHAKA)
    res = is_dse_market_open(sun_open, settings=cfg)
    assert res["is_open"] is True
    assert res["is_trading_day"] is True
    assert "open for live trading" in res["reason"]

    # Friday (weekday=4) at 11:00 AM -> Weekend Closed
    fri_closed = datetime(2026, 11, 6, 11, 0, 0, tzinfo=DHAKA)
    res_fri = is_dse_market_open(fri_closed, settings=cfg)
    assert res_fri["is_open"] is False
    assert res_fri["is_trading_day"] is False
    assert "Weekend" in res_fri["reason"]

    # Sunday 9:30 AM -> Pre-market
    sun_pre = datetime(2026, 11, 8, 9, 30, 0, tzinfo=DHAKA)
    res_pre = is_dse_market_open(sun_pre, settings=cfg)
    assert res_pre["is_open"] is False
    assert "Pre-market" in res_pre["reason"]

    # Sunday 3:00 PM -> Post-market
    sun_post = datetime(2026, 11, 8, 15, 0, 0, tzinfo=DHAKA)
    res_post = is_dse_market_open(sun_post, settings=cfg)
    assert res_post["is_open"] is False
    assert "Post-market" in res_post["reason"]

    # Holiday
    cfg_holiday = Settings(holidays=frozenset({date(2026, 11, 8)}))
    res_hol = is_dse_market_open(sun_open, settings=cfg_holiday)
    assert res_hol["is_open"] is False
    assert "DSE holiday" in res_hol["reason"]


def test_scheduler_lifecycle_and_tick(tmp_path):
    async def _run():
        db_file = tmp_path / "sched_test.db"
        settings = Settings(database_url=f"sqlite:///{db_file}")
        database = Database(settings.database_url)
        database.create_schema()
        with database.write() as session:
            seed_demo(session, settings)

        scheduler = DSEMarketScheduler(database, settings)
        status = scheduler.get_status()
        assert status["running"] is False
        assert "market" in status

        # Run scheduled tick with force=True
        tick_res = await scheduler.run_scheduled_tick(force=True)
        assert tick_res["status"] == "EXECUTED"
        assert scheduler.tick_count == 1
        assert scheduler.last_tick_at is not None

        # Start and stop scheduler
        start_res = scheduler.start()
        assert start_res["status"] == "STARTED"
        assert scheduler.running is True

        stop_res = await scheduler.stop()
        assert stop_res["status"] == "STOPPED"
        assert scheduler.running is False

    asyncio.run(_run())


def test_stocknow_scheduler_api_endpoints(tmp_path):
    db_file = tmp_path / "sched_api_test.db"
    settings = Settings(database_url=f"sqlite:///{db_file}")
    app = create_app(settings)

    with TestClient(app, base_url="http://localhost") as client:
        # GET /api/stocknow/scheduler
        resp = client.get("/api/stocknow/scheduler")
        assert resp.status_code == 200
        data = resp.json()
        assert "running" in data
        assert "market" in data

        # POST /api/stocknow/scheduler tick_now (forced)
        resp_tick = client.post("/api/stocknow/scheduler", json={"action": "tick_now", "force": True})
        assert resp_tick.status_code == 200
        tick_data = resp_tick.json()
        assert tick_data["status"] == "EXECUTED"

        # POST /api/stocknow/scheduler start
        resp_start = client.post("/api/stocknow/scheduler", json={"action": "start"})
        assert resp_start.status_code == 200
        assert resp_start.json()["status"] == "STARTED"

        # POST /api/stocknow/scheduler stop
        resp_stop = client.post("/api/stocknow/scheduler", json={"action": "stop"})
        assert resp_stop.status_code == 200
        assert resp_stop.json()["status"] == "STOPPED"


def test_hermes_scheduler_commands(tmp_path):
    db_file = tmp_path / "sched_hermes_test.db"
    settings = Settings(database_url=f"sqlite:///{db_file}")
    app = create_app(settings)

    with TestClient(app, base_url="http://localhost") as client:
        # Start DSE scheduler command
        resp_start = client.post("/api/chat", json={"message": "start dse scheduler"})
        assert resp_start.status_code == 200
        reply_start = resp_start.json()["reply"]
        assert "DSE" in reply_start

        # Run scheduler tick now
        resp_tick = client.post("/api/chat", json={"message": "run scheduler tick now"})
        assert resp_tick.status_code == 200
        reply_tick = resp_tick.json()["reply"]
        assert "Scheduler" in reply_tick or "টিক" in reply_tick

        # Stop scheduler command
        resp_stop = client.post("/api/chat", json={"message": "stop dse scheduler"})
        assert resp_stop.status_code == 200
        reply_stop = resp_stop.json()["reply"]
        assert "DSE" in reply_stop
