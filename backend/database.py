"""Durable paper ledger, with one transaction for each mutation/cycle."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from threading import RLock
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    create_engine,
    event,
    text,
)
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.config import utc_now_iso

MONEY = Numeric(18, 2)
PRICE = Numeric(18, 4)
PERCENT = Numeric(8, 4)


class Base(DeclarativeBase):
    pass


class PortfolioState(Base):
    __tablename__ = "portfolio_state"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    name: Mapped[str] = mapped_column(String(80), default="Humming Bird")
    mode: Mapped[str] = mapped_column(String(16), default="DEMO")
    initial_capital: Mapped[Decimal] = mapped_column(MONEY)
    clock_date: Mapped[date] = mapped_column(Date)
    revision: Mapped[int] = mapped_column(Integer, default=1)
    rules_revision: Mapped[int] = mapped_column(Integer, default=1)
    paused: Mapped[bool] = mapped_column(Boolean, default=False)
    automation_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    ingestion_mode: Mapped[str] = mapped_column(String(32), default="BACKGROUND_POLLING")
    polling_interval_sec: Mapped[int] = mapped_column(Integer, default=120)
    calendar_holidays: Mapped[list[str]] = mapped_column(JSON, default=list)
    bucket_anchor: Mapped[date] = mapped_column(Date)
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class CompanyProfile(Base):
    __tablename__ = "company_profiles"
    symbol: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    sector: Mapped[str] = mapped_column(String(32))
    favorite: Mapped[bool] = mapped_column(Boolean, default=True)
    settlement_days: Mapped[int] = mapped_column(Integer, default=2)
    last_price: Mapped[Decimal] = mapped_column(PRICE)
    price_history: Mapped[list[dict[str, str]]] = mapped_column(JSON)
    quote_on: Mapped[date] = mapped_column(Date)
    source: Mapped[str] = mapped_column(String(32), default="DEMO_SEED")
    watchlist_category: Mapped[str] = mapped_column(String(32), default="GSC")  # GSC, GSC_L1, GSC_L2
    quarantined: Mapped[bool] = mapped_column(Boolean, default=False)
    quarantine_reason: Mapped[str] = mapped_column(String(500), default="")


class CustomRule(Base):
    __tablename__ = "custom_rules"
    symbol: Mapped[str] = mapped_column(ForeignKey("company_profiles.symbol"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    buy_allocation_pct: Mapped[Decimal] = mapped_column(PERCENT)
    profit_tiers: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["1.5", "3.5", "6.0"])
    tier_slices: Mapped[list[str]] = mapped_column(JSON, default=lambda: ["25", "25", "25"])
    pullback_pct: Mapped[Decimal] = mapped_column(PERCENT, default=Decimal("3"))
    buy_zone_fraction: Mapped[Decimal] = mapped_column(PERCENT, default=Decimal("0.35"))
    crash_daily_pct: Mapped[Decimal] = mapped_column(PERCENT, default=Decimal("8"))
    crash_drawdown_pct: Mapped[Decimal] = mapped_column(PERCENT, default=Decimal("15"))
    __table_args__ = (CheckConstraint("buy_allocation_pct >= 0 AND buy_allocation_pct <= 100"),)


class TaxLot(Base):
    __tablename__ = "tax_lots"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("company_profiles.symbol"))
    bucket: Mapped[str] = mapped_column(String(1))
    acquired_on: Mapped[date] = mapped_column(Date)
    matures_on: Mapped[date] = mapped_column(Date)
    original_qty: Mapped[int] = mapped_column(Integer)
    remaining_qty: Mapped[int] = mapped_column(Integer)
    buy_price: Mapped[Decimal] = mapped_column(PRICE)
    buy_fee: Mapped[Decimal] = mapped_column(MONEY)
    original_cost_basis: Mapped[Decimal] = mapped_column(MONEY)
    remaining_cost_basis: Mapped[Decimal] = mapped_column(MONEY)
    cycle_base_qty: Mapped[int] = mapped_column(Integer)
    next_tier: Mapped[int] = mapped_column(Integer, default=0)
    last_sale_revision: Mapped[int] = mapped_column(Integer, default=0)
    peak_price: Mapped[Decimal] = mapped_column(PRICE)
    phase: Mapped[str] = mapped_column(String(24), default="ACTIVE")
    recovery_anchor: Mapped[Decimal | None] = mapped_column(PRICE, nullable=True)
    __table_args__ = (
        CheckConstraint("original_qty > 0 AND remaining_qty >= 0 AND remaining_qty <= original_qty"),
        CheckConstraint("remaining_cost_basis >= 0 AND original_cost_basis > 0"),
        CheckConstraint("cycle_base_qty > 0 AND next_tier >= 0"),
        CheckConstraint("bucket IN ('A', 'B', 'C')"),
        Index("ix_lot_symbol_maturity", "symbol", "matures_on"),
    )


class AutomationCycle(Base):
    __tablename__ = "automation_cycles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    request_id: Mapped[str | None] = mapped_column(String(36), unique=True, nullable=True)
    signal_key: Mapped[str] = mapped_column(String(100), unique=True)
    session_on: Mapped[date] = mapped_column(Date)
    market_revision: Mapped[int] = mapped_column(Integer)
    rules_revision: Mapped[int] = mapped_column(Integer)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class TradeLog(Base):
    __tablename__ = "trade_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    trade_key: Mapped[str] = mapped_column(String(160), unique=True)
    cycle_id: Mapped[str | None] = mapped_column(ForeignKey("automation_cycles.id"), nullable=True)
    lot_id: Mapped[int] = mapped_column(ForeignKey("tax_lots.id"))
    symbol: Mapped[str] = mapped_column(ForeignKey("company_profiles.symbol"))
    side: Mapped[str] = mapped_column(String(4))
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(PRICE)
    gross_amount: Mapped[Decimal] = mapped_column(MONEY)
    fee: Mapped[Decimal] = mapped_column(MONEY)
    net_cash_change: Mapped[Decimal] = mapped_column(MONEY)
    realized_pnl: Mapped[Decimal] = mapped_column(MONEY, default=Decimal("0"))
    bucket: Mapped[str] = mapped_column(String(1))
    trade_on: Mapped[date] = mapped_column(Date)
    settles_on: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(String(500))
    source: Mapped[str] = mapped_column(String(32), default="DEMO_PAPER")
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)
    __table_args__ = (
        CheckConstraint("quantity > 0 AND price > 0 AND fee >= 0"),
        CheckConstraint("side IN ('BUY', 'SELL')"),
        CheckConstraint("side != 'SELL' OR realized_pnl >= 0"),
        Index("ix_trade_symbol_date", "symbol", "trade_on"),
    )


class CanaryThesis(Base):
    __tablename__ = "canary_theses"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("company_profiles.symbol"), index=True)
    thesis: Mapped[str] = mapped_column(String(500))
    created_on: Mapped[date] = mapped_column(Date)
    entry_price: Mapped[Decimal] = mapped_column(PRICE)
    canary_qty: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default="OBSERVING")  # OBSERVING, CONFIRMED_LOSS, FALSE_ALARM_STABLE, RESOLVED
    observations_count: Mapped[int] = mapped_column(Integer, default=0)
    last_price_observed: Mapped[Decimal] = mapped_column(PRICE)
    notes: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class HermesSkillRevision(Base):
    __tablename__ = "hermes_skill_revisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    skill_name: Mapped[str] = mapped_column(String(64), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[str] = mapped_column(String(500))
    patch_diff: Mapped[str] = mapped_column(String(2000), default="")
    session_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class HermesUserProfile(Base):
    __tablename__ = "hermes_user_profile"
    id: Mapped[int] = mapped_column(primary_key=True, default=1)
    operator_name: Mapped[str] = mapped_column(String(64), default="Hasibur")
    language_preference: Mapped[str] = mapped_column(String(32), default="Bangla/Banglish")
    risk_posture: Mapped[str] = mapped_column(String(64), default="Strict No-Loss / Capital Preservation")
    custom_directives: Mapped[list[str]] = mapped_column(JSON, default=lambda: [
        "Never panic sell at a loss",
        "Lock 90% profit on severe bad news, keep 10% canary probe",
        "Respect T+2 working day calendar",
    ])
    updated_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class HermesSessionMemory(Base):
    __tablename__ = "hermes_session_memory"
    id: Mapped[int] = mapped_column(primary_key=True)
    session_date: Mapped[date] = mapped_column(Date, index=True)
    role: Mapped[str] = mapped_column(String(16))
    content: Mapped[str] = mapped_column(String(4000))
    symbol_mentioned: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    action_taken: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class HermesDurableFact(Base):
    __tablename__ = "hermes_durable_facts"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("company_profiles.symbol"), index=True)
    category: Mapped[str] = mapped_column(String(32), default="FUNDAMENTAL")
    fact: Mapped[str] = mapped_column(String(1000))
    confidence: Mapped[str] = mapped_column(String(16), default="HIGH")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class HermesStateCheckpoint(Base):
    __tablename__ = "hermes_state_checkpoints"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    action: Mapped[str] = mapped_column(String(64))
    description: Mapped[str] = mapped_column(String(500))
    snapshot_payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    session_on: Mapped[date] = mapped_column(Date)
    reverted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class CycleRequestKey(Base):
    __tablename__ = "cycle_request_keys"
    request_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    cycle_id: Mapped[str] = mapped_column(ForeignKey("automation_cycles.id"))


class DecisionLog(Base):
    __tablename__ = "decision_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    cycle_id: Mapped[str] = mapped_column(ForeignKey("automation_cycles.id"), index=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("company_profiles.symbol"))
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("tax_lots.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(40))
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reason: Mapped[str] = mapped_column(String(600))
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class RuleAudit(Base):
    __tablename__ = "rule_audit"
    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str] = mapped_column(ForeignKey("company_profiles.symbol"))
    before: Mapped[dict[str, Any]] = mapped_column(JSON)
    after: Mapped[dict[str, Any]] = mapped_column(JSON)
    session_on: Mapped[date] = mapped_column(Date)
    created_at: Mapped[str] = mapped_column(String(40), default=utc_now_iso)


class ChatBudget(Base):
    __tablename__ = "chat_budget"
    day: Mapped[date] = mapped_column(Date, primary_key=True)
    calls: Mapped[int] = mapped_column(Integer, default=0)


class Database:
    def __init__(self, url: str):
        parsed = make_url(url)
        if parsed.drivername != "sqlite":
            raise ValueError("Sprint 1 supports a local SQLite URL only.")
        if parsed.database and parsed.database != ":memory:":
            Path(parsed.database).expanduser().parent.mkdir(parents=True, exist_ok=True)
        options: dict[str, Any] = {"connect_args": {"check_same_thread": False, "timeout": 15}}
        if parsed.database in {None, "", ":memory:"}:
            options["poolclass"] = StaticPool
        self.engine = create_engine(url, **options)
        self.lock = RLock()

        @event.listens_for(self.engine, "connect")
        def configure_sqlite(connection: Any, _record: Any) -> None:
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=15000")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

        self.sessions = sessionmaker(self.engine, expire_on_commit=False)

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)
        with self.engine.connect() as conn:
            result = conn.execute(text("PRAGMA table_info(company_profiles)"))
            cols = [row[1] for row in result.fetchall()]
            if "watchlist_category" not in cols:
                conn.execute(text("ALTER TABLE company_profiles ADD COLUMN watchlist_category VARCHAR(32) DEFAULT 'GSC'"))
                conn.commit()

            result = conn.execute(text("PRAGMA table_info(portfolio_state)"))
            ps_cols = [row[1] for row in result.fetchall()]
            if ps_cols:
                if "automation_enabled" not in ps_cols:
                    conn.execute(text("ALTER TABLE portfolio_state ADD COLUMN automation_enabled BOOLEAN DEFAULT 1"))
                if "ingestion_mode" not in ps_cols:
                    conn.execute(text("ALTER TABLE portfolio_state ADD COLUMN ingestion_mode VARCHAR(32) DEFAULT 'BACKGROUND_POLLING'"))
                if "polling_interval_sec" not in ps_cols:
                    conn.execute(text("ALTER TABLE portfolio_state ADD COLUMN polling_interval_sec INTEGER DEFAULT 120"))
                conn.commit()

    @contextmanager
    def read(self):
        # A single explicit read transaction gives a coherent multi-query snapshot.
        with self.sessions() as session:
            session.execute(text("BEGIN"))
            try:
                yield session
            finally:
                session.rollback()

    @contextmanager
    def write(self):
        with self.lock, self.sessions() as session:
            session.execute(text("BEGIN IMMEDIATE"))
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise


def portfolio_state(session: Session) -> PortfolioState:
    state = session.get(PortfolioState, 1)
    if state is None:
        raise RuntimeError("Demo database is not initialized.")
    return state
