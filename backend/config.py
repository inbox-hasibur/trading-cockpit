"""Explicit demo assumptions. Nothing in this file enables connected trading."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DHAKA = ZoneInfo("Asia/Dhaka")
VERSION = "0.01"
DEFAULT_DATABASE_URL = f"sqlite:///{(ROOT / 'backend/data/hummingbird.db').as_posix()}"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class Settings:
    database_url: str = DEFAULT_DATABASE_URL
    trading_mode: str = "DEMO"
    initial_capital: Decimal = Decimal("15000.00")
    demo_start_date: date | None = None
    buy_fee_rate: Decimal = Decimal("0.005")
    sell_fee_rate: Decimal = Decimal("0.005")
    settlement_days: int = 2
    min_buy_notional: Decimal = Decimal("100.00")
    holidays: frozenset[date] = frozenset()
    market_open: time = time(10, 0)
    market_close: time = time(14, 30)
    bucket_anchor: date = date(2024, 1, 7)  # Fixed Sunday; not a resettable weekday.
    openrouter_api_key: str = ""
    openrouter_model: str = "xiaomi/mimo-v2.6-pro"
    gemini_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    operator_username: str = ""
    operator_password: str = ""
    operator_name: str = "Hasibur Rahman"
    operator_portfolio: str = "Humming Bird (StockNow)"
    stocknow_live_portfolio_id: str = "164580"
    stocknow_test_portfolio_id: str = ""
    chat_daily_call_limit: int = 30
    chat_max_output_tokens: int = 500
    cockpit_api_token: str = ""
    trusted_hosts: tuple[str, ...] = ("localhost", "127.0.0.1")

    @property
    def operator_phone(self) -> str:
        return self.operator_username

    @property
    def stocknow_mobile(self) -> str:
        return self.operator_username

    @property
    def stocknow_password(self) -> str:
        return self.operator_password

    def __post_init__(self) -> None:
        if self.trading_mode != "DEMO":
            raise ValueError("Only DEMO mode exists in Sprint 1. Live/StockNow orders are disabled.")
        if not self.initial_capital.is_finite() or self.initial_capital < 1000:
            raise ValueError("INITIAL_CAPITAL must be finite and at least 1000 BDT.")
        for rate in (self.buy_fee_rate, self.sell_fee_rate):
            if not rate.is_finite() or not Decimal(0) <= rate < Decimal("0.1"):
                raise ValueError("Fee rates must be decimal fractions from 0 to less than 0.1.")
        if not 1 <= self.settlement_days <= 10:
            raise ValueError("SETTLEMENT_DAYS must be between 1 and 10 for this demo.")
        if not self.min_buy_notional.is_finite() or self.min_buy_notional <= 0:
            raise ValueError("MIN_BUY_NOTIONAL must be positive and finite.")
        if self.market_open >= self.market_close:
            raise ValueError("MARKET_CLOSE must be after MARKET_OPEN.")
        if not 0 <= self.chat_daily_call_limit <= 1000:
            raise ValueError("CHAT_DAILY_CALL_LIMIT must be 0–1000.")
        if not 100 <= self.chat_max_output_tokens <= 2000:
            raise ValueError("CHAT_MAX_OUTPUT_TOKENS must be 100–2000.")
        if self.cockpit_api_token and len(self.cockpit_api_token) < 16:
            raise ValueError("COCKPIT_API_TOKEN must contain at least 16 characters.")
        if not self.trusted_hosts or any("*" in host for host in self.trusted_hosts):
            raise ValueError("Use explicit TRUSTED_HOSTS; wildcards are not allowed.")
        if any(host not in {"localhost", "127.0.0.1", "[::1]"} for host in self.trusted_hosts):
            if not self.cockpit_api_token:
                raise ValueError("Non-loopback TRUSTED_HOSTS require COCKPIT_API_TOKEN.")

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv(ROOT / ".env", override=False)
        load_dotenv(ROOT / "backend/.env", override=False)
        start = os.getenv("DEMO_START_DATE", "").strip()
        holidays = frozenset(
            date.fromisoformat(value.strip())
            for value in os.getenv("DSE_HOLIDAYS", "").split(",")
            if value.strip()
        )
        mobile = os.getenv("STOCKNOW_MOBILE", "").strip() or os.getenv("OPERATOR_USERNAME", "").strip()
        password = os.getenv("STOCKNOW_PASSWORD", "").strip() or os.getenv("OPERATOR_PASSWORD", "").strip()
        return cls(
            database_url=os.getenv("DATABASE_URL", "").strip() or DEFAULT_DATABASE_URL,
            trading_mode=os.getenv("TRADING_MODE", "DEMO").strip().upper(),
            initial_capital=Decimal(os.getenv("INITIAL_CAPITAL", "15000")),
            demo_start_date=date.fromisoformat(start) if start else None,
            buy_fee_rate=Decimal(os.getenv("BUY_FEE_RATE", "0.005")),
            sell_fee_rate=Decimal(os.getenv("SELL_FEE_RATE", "0.005")),
            settlement_days=int(os.getenv("SETTLEMENT_DAYS", "2")),
            min_buy_notional=Decimal(os.getenv("MIN_BUY_NOTIONAL", "100")),
            holidays=holidays,
            market_open=time.fromisoformat(os.getenv("MARKET_OPEN", "10:00")),
            market_close=time.fromisoformat(os.getenv("MARKET_CLOSE", "14:30")),
            openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
            openrouter_model=os.getenv("OPENROUTER_MODEL", "xiaomi/mimo-v2.6-pro").strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip() or os.getenv("GOOGLE_API_KEY", "").strip(),
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID", "").strip(),
            operator_username=mobile,
            operator_password=password,
            operator_name=os.getenv("OPERATOR_NAME", "Hasibur Rahman").strip(),
            operator_portfolio=os.getenv("OPERATOR_PORTFOLIO", "Humming Bird (StockNow)").strip(),
            stocknow_live_portfolio_id=os.getenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580").strip(),
            stocknow_test_portfolio_id=os.getenv("STOCKNOW_TEST_PORTFOLIO_ID", "").strip(),
            chat_daily_call_limit=int(os.getenv("CHAT_DAILY_CALL_LIMIT", "30")),
            chat_max_output_tokens=int(os.getenv("CHAT_MAX_OUTPUT_TOKENS", "500")),
            cockpit_api_token=os.getenv("COCKPIT_API_TOKEN", "").strip(),
            trusted_hosts=tuple(
                host.strip()
                for host in os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")
                if host.strip()
            ),
        )


def get_allowed_portfolios(settings: Settings | None = None) -> tuple[str, ...]:
    """Returns the allowlist of authorized StockNow portfolio IDs: [LIVE, TEST]."""
    if settings is None:
        try:
            settings = Settings.from_env()
        except Exception:
            live = os.getenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580").strip()
            test = os.getenv("STOCKNOW_TEST_PORTFOLIO_ID", "").strip()
            res = [live]
            if test and test not in res:
                res.append(test)
            return tuple(res)
    live = settings.stocknow_live_portfolio_id.strip()
    test = settings.stocknow_test_portfolio_id.strip()
    res = [live]
    if test and test not in res:
        res.append(test)
    return tuple(res)


def get_active_target_portfolio(trading_mode: str, settings: Settings | None = None) -> str | None:
    """Returns the active portfolio ID based on current trading mode:
    - LIVE_HOURS -> STOCKNOW_LIVE_PORTFOLIO_ID (default 164580)
    - TEST_OFFHOURS -> STOCKNOW_TEST_PORTFOLIO_ID (or None if unconfigured)
    """
    if settings is None:
        try:
            settings = Settings.from_env()
        except Exception:
            if trading_mode == "LIVE_HOURS":
                return os.getenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580").strip()
            return os.getenv("STOCKNOW_TEST_PORTFOLIO_ID", "").strip() or None

    if trading_mode == "LIVE_HOURS":
        return settings.stocknow_live_portfolio_id.strip()
    return settings.stocknow_test_portfolio_id.strip() or None


def get_portfolio_name(portfolio_id: str, settings: Settings | None = None) -> str:
    """Returns human-readable portfolio name for a given portfolio ID."""
    live_id = "164580"
    test_id = ""
    live_name = "Humming Bird"
    if settings:
        live_id = settings.stocknow_live_portfolio_id.strip()
        test_id = settings.stocknow_test_portfolio_id.strip()
        live_name = getattr(settings, "operator_portfolio", "Humming Bird")
    else:
        live_id = os.getenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580").strip()
        test_id = os.getenv("STOCKNOW_TEST_PORTFOLIO_ID", "").strip()

    pid = str(portfolio_id).strip()
    if pid == live_id:
        return live_name
    elif test_id and pid == test_id:
        return f"{live_name} (Test)"
    return f"Portfolio #{pid}"


def test_portfolio_configured(settings: Settings | None = None) -> bool:
    """Returns False when the test portfolio id is empty or equal to the live id."""
    if settings is not None:
        live = settings.stocknow_live_portfolio_id.strip()
        test = settings.stocknow_test_portfolio_id.strip()
    else:
        live = os.getenv("STOCKNOW_LIVE_PORTFOLIO_ID", "164580").strip()
        test = os.getenv("STOCKNOW_TEST_PORTFOLIO_ID", "").strip()
    if not test:
        return False
    return test != live


