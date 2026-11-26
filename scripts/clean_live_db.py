"""Safe Live DB Sanitizer for TradeXpress V1 (Zero-Dummy Policy).

Creates an atomic SQLite backup first, then purges legacy StockNow #164580
holdings/trades/shadow orders and fake DEMO_SEED price curves from
backend/data/hummingbird.db, leaving the live cockpit in clean SHADOW_DUMMY mode.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy import delete, or_, update
from sqlalchemy.orm.attributes import flag_modified

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.database import (
    CanaryThesis,
    CompanyProfile,
    CycleRequestKey,
    Database,
    DecisionLog,
    OrderIdempotencyKey,
    ShadowOrder,
    TaxLot,
    TradeLog,
    portfolio_state,
)
from scripts.backup_db import backup_database, get_default_db_path


def clean_live_database(db_path: Path | None = None, create_backup: bool = True) -> dict[str, object]:
    """Sanitizes the live SQLite database into zero-dummy SHADOW_DUMMY state."""
    target_path = (db_path or get_default_db_path()).resolve()
    if not target_path.exists():
        return {"ok": False, "reason": f"Database not found: {target_path}"}

    backup_path: Path | None = None
    if create_backup:
        backup_path = backup_database(db_path=target_path, verbose=True)

    db = Database(f"sqlite:///{target_path.as_posix()}")
    db.create_schema()

    cleared_curves = 0
    with db.write() as session:
        state = portfolio_state(session)

        # Unlink DecisionLog.lot_id before deleting TaxLot rows
        session.execute(update(DecisionLog).values(lot_id=None))

        # Wipe legacy #164580 / DEMO_SEED / STOCKNOW_LIVE records & stale canary_theses
        legacy_pids = ("164580", "DEMO_SEED", "STOCKNOW_LIVE", "")
        session.execute(delete(CanaryThesis))
        session.execute(delete(OrderIdempotencyKey))
        session.execute(delete(CycleRequestKey))
        session.execute(delete(ShadowOrder))
        session.execute(
            delete(TradeLog).where(
                or_(
                    TradeLog.portfolio_id.in_(legacy_pids),
                    TradeLog.source.in_(("DEMO_SEED", "STOCKNOW_LIVE", "SEED")),
                )
            )
        )
        session.execute(delete(TaxLot).where(TaxLot.portfolio_id.in_(legacy_pids)))

        # Clear any synthetic/seeded price_history and strip legacy dummy suffixes from company names
        clean_name_overrides = {
            "GP": "Grameenphone Ltd.",
            "BXPHARMA": "Beximco Pharmaceuticals Ltd.",
            "SQURPHARMA": "Square Pharmaceuticals PLC",
            "BANKASIA": "Bank Asia PLC",
            "EXIM1STMF": "EXIM Bank 1st Mutual Fund",
        }
        dummy_suffixes = (" · Demo", " · Crash", " · Cra", " · Rally", " · Pullback", " · Normal", " · Recovery")
        for cp in session.scalars(__import__("sqlalchemy").select(CompanyProfile)):
            if cp.symbol in clean_name_overrides and any(s in (cp.name or "") for s in dummy_suffixes):
                cp.name = clean_name_overrides[cp.symbol]
            elif cp.name:
                for suf in dummy_suffixes:
                    if suf in cp.name:
                        cp.name = cp.name.replace(suf, "").strip()
            if getattr(cp, "source", "") in ("DEMO_SEED", "STOCKNOW_FAVORITES"):
                cp.price_history = []
                flag_modified(cp, "price_history")
                cp.source = "TRADEXPRESS_PENDING"
                cleared_curves += 1

        # Reset PortfolioState cleanly to SHADOW_DUMMY zero-dummy baseline
        state.mode = "SHADOW"
        state.execution_venue = "SHADOW_DUMMY"
        state.name = "TradeXpress H9210 Shadow"
        state.initial_capital = Decimal("0.00")
        state.unsettled_sales_bdt = Decimal("0.00")
        state.automation_enabled = False
        state.paused = False
        state.circuit_breaker_tripped = False
        state.consecutive_failure_count = 0
        state.circuit_breaker_reason = None
        state.startup_health_passed = True
        state.startup_health_status = "READY"
        session.flush()

    return {
        "ok": True,
        "db_path": str(target_path),
        "backup_path": str(backup_path) if backup_path else None,
        "cleared_curves": cleared_curves,
    }


if __name__ == "__main__":
    res = clean_live_database()
    print(res)
