"""Database and state checkpoint manager for atomic rollbacks."""

from __future__ import annotations

import time
from datetime import date
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.database import (
    CompanyProfile,
    CustomRule,
    HermesStateCheckpoint,
    PortfolioState,
    TaxLot,
    TradeLog,
)
from backend.engine.money import decimal
from backend.engine.t2_ledger import assert_ledger


class CheckpointManager:
    """Manages transactional state checkpoints and atomic rollback restoration."""

    @staticmethod
    def create_checkpoint(
        session: Session,
        state: PortfolioState,
        action: str,
        description: str,
        symbol: str | None = None,
        diff_payload: dict[str, Any] | None = None,
        actor: str = "Kernel API",
        extra_snapshot: dict[str, Any] | None = None,
    ) -> HermesStateCheckpoint:
        payload: dict[str, Any] = {
            "action": action,
            "description": description,
            "date": state.clock_date.isoformat(),
            "rules_revision": state.rules_revision,
            "automation_enabled": getattr(state, "automation_enabled", True),
            "ingestion_mode": getattr(state, "ingestion_mode", "BACKGROUND_POLLING"),
            "polling_interval_sec": getattr(state, "polling_interval_sec", 120),
            "companies": {},
            "rules": {},
        }
        if extra_snapshot:
            payload.update(extra_snapshot)
        symbols_to_save = [symbol.upper()] if symbol else [c.symbol for c in session.scalars(select(CompanyProfile))]
        for sym in symbols_to_save:
            comp = session.get(CompanyProfile, sym)
            rule = session.get(CustomRule, sym)
            if comp:
                payload["companies"][sym] = {
                    "quarantined": comp.quarantined,
                    "quarantine_reason": comp.quarantine_reason,
                    "watchlist_category": getattr(comp, "watchlist_category", "GSC"),
                    "last_price": str(comp.last_price),
                }
            if rule:
                payload["rules"][sym] = {
                    "buy_allocation_pct": str(rule.buy_allocation_pct),
                    "enabled": rule.enabled,
                }

        cp = HermesStateCheckpoint(
            id=f"{time.time_ns():020d}_{uuid4().hex[:8]}",
            action=action,
            description=description,
            snapshot_payload=payload,
            diff_payload=diff_payload,
            actor=actor,
            session_on=state.clock_date,
            reverted=False,
        )
        session.add(cp)
        session.flush()
        return cp

    @staticmethod
    def rollback_last(session: Session, state: PortfolioState) -> dict[str, Any]:
        cp = session.scalar(
            select(HermesStateCheckpoint)
            .where(HermesStateCheckpoint.reverted == False)
            .order_by(HermesStateCheckpoint.id.desc())
            .limit(1)
        )
        if not cp:
            raise ValueError("No active checkpoint available to rollback.")

        payload = cp.snapshot_payload
        restored_symbols = []
        for sym, data in payload.get("companies", {}).items():
            comp = session.get(CompanyProfile, sym)
            if comp:
                comp.quarantined = data["quarantined"]
                comp.quarantine_reason = data["quarantine_reason"]
                comp.watchlist_category = data.get("watchlist_category", "GSC")
                restored_symbols.append(sym)

        for sym, rdata in payload.get("rules", {}).items():
            rule = session.get(CustomRule, sym)
            if rule:
                rule.buy_allocation_pct = decimal(rdata["buy_allocation_pct"])
                rule.enabled = rdata["enabled"]

        if "automation_enabled" in payload:
            state.automation_enabled = payload["automation_enabled"]
            state.paused = not state.automation_enabled
        if "ingestion_mode" in payload:
            state.ingestion_mode = payload["ingestion_mode"]
        if "polling_interval_sec" in payload:
            state.polling_interval_sec = payload["polling_interval_sec"]

        portfolio_lots = payload.get("portfolio_lots")
        portfolio_trades = payload.get("portfolio_trades")
        if portfolio_lots is not None and portfolio_trades is not None:
            session.query(TradeLog).delete()
            session.query(TaxLot).delete()
            session.flush()

            for ldata in portfolio_lots:
                lot = TaxLot(
                    id=ldata["id"],
                    symbol=ldata["symbol"],
                    bucket=ldata["bucket"],
                    acquired_on=date.fromisoformat(ldata["acquired_on"]),
                    matures_on=date.fromisoformat(ldata["matures_on"]),
                    original_qty=ldata["original_qty"],
                    remaining_qty=ldata["remaining_qty"],
                    buy_price=decimal(ldata["buy_price"]),
                    buy_fee=decimal(ldata["buy_fee"]),
                    original_cost_basis=decimal(ldata["original_cost_basis"]),
                    remaining_cost_basis=decimal(ldata["remaining_cost_basis"]),
                    cycle_base_qty=ldata["cycle_base_qty"],
                    next_tier=ldata.get("next_tier", 0),
                    last_sale_revision=ldata.get("last_sale_revision", 0),
                    peak_price=decimal(ldata["peak_price"]),
                    phase=ldata.get("phase", "ACTIVE"),
                    recovery_anchor=decimal(ldata["recovery_anchor"]) if ldata.get("recovery_anchor") else None,
                )
                session.add(lot)
            session.flush()

            for tdata in portfolio_trades:
                trade = TradeLog(
                    id=tdata["id"],
                    trade_key=tdata["trade_key"],
                    cycle_id=tdata.get("cycle_id"),
                    lot_id=tdata["lot_id"],
                    symbol=tdata["symbol"],
                    side=tdata["side"],
                    quantity=tdata["quantity"],
                    price=decimal(tdata["price"]),
                    gross_amount=decimal(tdata["gross_amount"]),
                    fee=decimal(tdata["fee"]),
                    net_cash_change=decimal(tdata["net_cash_change"]),
                    realized_pnl=decimal(tdata.get("realized_pnl", "0")),
                    bucket=tdata["bucket"],
                    trade_on=date.fromisoformat(tdata["trade_on"]),
                    settles_on=date.fromisoformat(tdata["settles_on"]),
                    reason=tdata.get("reason", ""),
                    source=tdata.get("source", "DEMO_SEED"),
                )
                session.add(trade)
            session.flush()

            if "initial_capital" in payload:
                state.initial_capital = decimal(payload["initial_capital"])
            assert_ledger(session, state)

        cp.reverted = True
        state.rules_revision += 1
        session.flush()
        return {
            "checkpoint_id": cp.id,
            "action_reverted": cp.action,
            "description": cp.description,
            "restored_symbols": restored_symbols,
        }

