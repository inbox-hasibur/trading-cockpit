"""Unit tests for TradeXpress foundation: symbols, safety, fees, and DSE schedule."""

from datetime import date, datetime, time
from decimal import Decimal
from zoneinfo import ZoneInfo
import pytest

from backend.adapters.base import (
    from_tradexpress_symbol,
    to_tradexpress_symbol,
    validate_tradexpress_order_safety,
    MarketQuote,
    OrderBookLevel,
    PortfolioHolding,
)
from backend.config import DHAKA, Settings
from backend.engine.money import (
    calculate_broker_fee_breakdown,
    money,
    round_trip_breakeven_price,
)
from backend.engine.scheduler import is_dse_market_open


class TestSymbolNormalization:
    def test_to_tradexpress_symbol_backtick(self):
        """to_tradexpress_symbol emits backtick board format."""
        assert to_tradexpress_symbol("BANKASIA") == "BANKASIA`PB"
        assert to_tradexpress_symbol("bankasia") == "BANKASIA`PB"
        assert to_tradexpress_symbol("MATINSPINN`PB") == "MATINSPINN`PB"
        assert to_tradexpress_symbol("GP'PB") == "GP`PB"
        assert to_tradexpress_symbol("PRIMEBANK", board="A") == "PRIMEBANK`A"

    def test_from_tradexpress_symbol_defensive(self):
        """from_tradexpress_symbol defensively strips backtick and apostrophe suffixes."""
        assert from_tradexpress_symbol("BANKASIA`PB") == "BANKASIA"
        assert from_tradexpress_symbol("BANKASIA'PB") == "BANKASIA"
        assert from_tradexpress_symbol("MATINSPINN`pb") == "MATINSPINN"
        assert from_tradexpress_symbol("GP") == "GP"


class TestOrderSafetyValidator:
    def test_valid_continuous_limit_order(self):
        """Valid Limit DAY order in Continuous session passes."""
        valid, errors = validate_tradexpress_order_safety(
            symbol="BANKASIA`PB",
            side="BUY",
            quantity=10,
            price=Decimal("17.90"),
            order_type="LIMIT",
            tif="DAY",
            all_or_none=False,
            settlement_type="PUBLIC",
            symbol_category="A",
            min_limit=Decimal("16.00"),
            max_limit=Decimal("19.50"),
            session_phase="CONTINUOUS",
        )
        assert valid is True
        assert errors == []

    def test_blocks_spot_and_z_category(self):
        """Rejects SPOT settlement and Z category securities."""
        valid_spot, errs_spot = validate_tradexpress_order_safety(
            symbol="TEST`PB",
            side="BUY",
            quantity=5,
            price=Decimal("10.00"),
            settlement_type="SPOT",
            symbol_category="A",
        )
        assert valid_spot is False
        assert any("SPOT settlement rejected" in e for e in errs_spot)

        valid_z, errs_z = validate_tradexpress_order_safety(
            symbol="TEST`PB",
            side="BUY",
            quantity=5,
            price=Decimal("10.00"),
            settlement_type="PUBLIC",
            symbol_category="Z",
        )
        assert valid_z is False
        assert any("Category 'Z' rejected" in e for e in errs_z)

    def test_blocks_market_and_gtc(self):
        """Rejects Market orders and non-DAY time-in-force."""
        valid, errs = validate_tradexpress_order_safety(
            symbol="TEST`PB",
            side="BUY",
            quantity=10,
            price=Decimal("10.00"),
            order_type="MARKET",
            tif="GTC",
            all_or_none=True,
        )
        assert valid is False
        assert any("LIMIT orders" in e for e in errs)
        assert any("DAY" in e for e in errs)
        assert any("All or None" in e for e in errs)

    def test_blocks_circuit_limit_violations(self):
        """Rejects limit prices violating exchange circuit limits."""
        valid_low, errs_low = validate_tradexpress_order_safety(
            symbol="TEST`PB",
            side="BUY",
            quantity=10,
            price=Decimal("15.00"),
            min_limit=Decimal("16.00"),
            max_limit=Decimal("20.00"),
        )
        assert valid_low is False
        assert any("below minimum circuit limit" in e for e in errs_low)

        valid_high, errs_high = validate_tradexpress_order_safety(
            symbol="TEST`PB",
            side="BUY",
            quantity=10,
            price=Decimal("21.00"),
            min_limit=Decimal("16.00"),
            max_limit=Decimal("20.00"),
        )
        assert valid_high is False
        assert any("exceeds maximum circuit limit" in e for e in errs_high)

    def test_post_closing_session_exact_ltp_rule(self):
        """In POST_CLOSING session, orders match strictly at exact LTP."""
        # Non-matching price rejected
        valid_diff, errs_diff = validate_tradexpress_order_safety(
            symbol="BANKASIA`PB",
            side="BUY",
            quantity=9,
            price=Decimal("18.00"),
            ltp=Decimal("17.90"),
            session_phase="POST_CLOSING",
        )
        assert valid_diff is False
        assert any("exact LTP matching" in e for e in errs_diff)

        # Matching price accepted
        valid_match, errs_match = validate_tradexpress_order_safety(
            symbol="BANKASIA`PB",
            side="BUY",
            quantity=9,
            price=Decimal("17.90"),
            ltp=Decimal("17.90"),
            session_phase="POST_CLOSING",
        )
        assert valid_match is True
        assert errs_match == []

    def test_offhours_na_fallback_handling(self):
        """Off-hours N/A fields accept valid cached fallbacks when allowed."""
        # Uncached N/A rejected
        valid_no_cache, errs_no_cache = validate_tradexpress_order_safety(
            symbol="TEST`PB",
            side="BUY",
            quantity=10,
            price=Decimal("10.00"),
            settlement_type="N/A",
            symbol_category="N/A",
            allow_offhours_na=False,
        )
        assert valid_no_cache is False

        # Cached fallback accepted
        valid_cached, errs_cached = validate_tradexpress_order_safety(
            symbol="TEST`PB",
            side="BUY",
            quantity=10,
            price=Decimal("10.00"),
            settlement_type="N/A",
            symbol_category="N/A",
            allow_offhours_na=True,
            cached_settlement_type="PUBLIC",
            cached_symbol_category="B",
        )
        assert valid_cached is True
        assert errs_cached == []


class TestFeeMathAndBreakdown:
    def test_calculate_broker_fee_breakdown(self):
        """Verifies exact gross, commission, VAT, and exchange fee math."""
        # Gross: 10,000 BDT, Comm: 0.40%, VAT: 15% on comm, Exchange: 0.05%
        res = calculate_broker_fee_breakdown(
            Decimal("10000.00"),
            commission_rate=Decimal("0.0040"),
            vat_rate=Decimal("0.15"),
            exchange_fee_rate=Decimal("0.0005"),
        )
        assert res["gross"] == Decimal("10000.00")
        assert res["commission"] == Decimal("40.00")
        assert res["vat"] == Decimal("6.00")
        assert res["exchange_fee"] == Decimal("5.00")
        assert res["total_fee"] == Decimal("51.00")
        assert res["effective_rate"] == Decimal("0.0051")

    def test_round_trip_breakeven_price(self):
        """Computes minimum exit price where net proceeds cover buy cost + both fees."""
        buy_price = Decimal("100.00")
        buy_fee = Decimal("0.005")   # 0.5%
        sell_fee = Decimal("0.005")  # 0.5%
        be_price = round_trip_breakeven_price(buy_price, buy_fee_rate=buy_fee, sell_fee_rate=sell_fee)
        
        # Total cost per share = 100 * 1.005 = 100.50
        # Net proceeds = be_price * 0.995
        # 101.01 * 0.995 = 100.50495 >= 100.50
        assert be_price == Decimal("101.01")
        total_buy_cost = buy_price * (Decimal("1") + buy_fee)
        net_sell_proceeds = be_price * (Decimal("1") - sell_fee)
        assert net_sell_proceeds >= total_buy_cost


class TestDSEScheduleTransitions:
    def test_schedule_continuous_phase(self):
        """10:00:00 to 13:59:59 is CONTINUOUS session."""
        sun_1000 = datetime(2026, 11, 8, 10, 0, 0, tzinfo=DHAKA)
        res_1000 = is_dse_market_open(sun_1000)
        assert res_1000["is_open"] is True
        assert res_1000["session_phase"] == "CONTINUOUS"

        sun_1359 = datetime(2026, 11, 8, 13, 59, 59, tzinfo=DHAKA)
        res_1359 = is_dse_market_open(sun_1359)
        assert res_1359["is_open"] is True
        assert res_1359["session_phase"] == "CONTINUOUS"

    def test_schedule_post_closing_phase(self):
        """14:00:00 to 14:10:00 is POST_CLOSING session."""
        sun_1400 = datetime(2026, 11, 8, 14, 0, 0, tzinfo=DHAKA)
        res_1400 = is_dse_market_open(sun_1400)
        assert res_1400["is_open"] is True
        assert res_1400["session_phase"] == "POST_CLOSING"

        sun_1405 = datetime(2026, 11, 8, 14, 5, 0, tzinfo=DHAKA)
        res_1405 = is_dse_market_open(sun_1405)
        assert res_1405["is_open"] is True
        assert res_1405["session_phase"] == "POST_CLOSING"

        sun_1410 = datetime(2026, 11, 8, 14, 10, 0, tzinfo=DHAKA)
        res_1410 = is_dse_market_open(sun_1410)
        assert res_1410["is_open"] is True
        assert res_1410["session_phase"] == "POST_CLOSING"

    def test_schedule_closed_phase(self):
        """Pre-market, post-14:10, and weekends are CLOSED."""
        sun_0959 = datetime(2026, 11, 8, 9, 59, 59, tzinfo=DHAKA)
        res_0959 = is_dse_market_open(sun_0959)
        assert res_0959["is_open"] is False
        assert res_0959["session_phase"] == "CLOSED"

        sun_1411 = datetime(2026, 11, 8, 14, 11, 0, tzinfo=DHAKA)
        res_1411 = is_dse_market_open(sun_1411)
        assert res_1411["is_open"] is False
        assert res_1411["session_phase"] == "CLOSED"

        fri_noon = datetime(2026, 11, 6, 12, 0, 0, tzinfo=DHAKA)
        res_fri = is_dse_market_open(fri_noon)
        assert res_fri["is_open"] is False
        assert res_fri["session_phase"] == "CLOSED"
