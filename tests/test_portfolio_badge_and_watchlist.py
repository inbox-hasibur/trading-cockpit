"""Tests for Portfolio Header Badge, Watchlist Curve Signals, and Ledger Row Tags."""

from pathlib import Path
import pytest

from backend.config import Settings
from backend.database import Database, TradeLog
from backend.portfolio import snapshot_from_session, trade_view
from backend.seed import seed_demo


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_badge.db"
    db = Database(f"sqlite:///{db_file}")
    db.create_schema()
    settings = Settings()
    with db.write() as session:
        seed_demo(session, settings)
    return db, settings


def test_trade_view_source_and_receipt_tagging(test_db):
    """Trade rows tag STOCKNOW_RECEIPT vs PAPER_FILL accurately."""
    db, settings = test_db
    with db.write() as session:
        trades = session.query(TradeLog).all()
        assert len(trades) > 0

        # Mark first trade as receipt and second as paper
        trades[0].source = "STOCKNOW_RECEIPT"
        session.flush()

        view1 = trade_view(trades[0])
        assert view1["source"] == "STOCKNOW_RECEIPT"

        view_paper = trade_view(trades[-1])
        assert view_paper["source"] in ("DEMO_SEED", "DEMO_PAPER", "PAPER_FILL")


def test_snapshot_metrics_includes_drift(test_db):
    """Snapshot metrics explicitly includes drift calculation."""
    db, settings = test_db
    with db.read() as session:
        snap = snapshot_from_session(session, settings)

        assert "drift" in snap["metrics"]
        assert isinstance(snap["metrics"]["drift"], float)
        assert snap["metrics"]["drift"] == 0.0


def test_html_portfolio_header_badge_and_footer():
    """Verify presence of portfolio-header-badge and footer-mode-tag in HTML."""
    html_path = Path("frontend/index.html")
    content = html_path.read_text(encoding="utf-8")

    # Header badge elements
    assert 'id="portfolio-header-badge"' in content
    assert 'id="portfolio-header-badge-text"' in content
    assert 'id="portfolio-header-badge-dot"' in content

    # Footer mode tag element
    assert 'id="footer-mode-tag"' in content
    assert "EXPERIMENTAL · DEMO ONLY" in content


def test_app_js_watchlist_invalid_data_replacement():
    """Verify app.js replaces red INVALID DATA with LIVE, LAST CLOSE, STALE, NO DATA and retry link."""
    js_path = Path("frontend/app.js")
    content = js_path.read_text(encoding="utf-8")

    # Check that app.js maps INVALID_DATA away
    assert 'displaySignal === "INVALID_DATA"' in content or 'INVALID' in content
    assert '"LAST_CLOSE"' in content
    assert '"NO_DATA"' in content
    assert '"STALE"' in content
    assert '"LIVE"' in content

    # Check retry sync link in watchlist
    assert 'retry-sync-link' in content
    assert '/api/stocknow/sync-market' in content

    # Check trade ledger row tagging
    assert '"STOCKNOW RECEIPT"' in content
    assert '"PAPER FILL"' in content
