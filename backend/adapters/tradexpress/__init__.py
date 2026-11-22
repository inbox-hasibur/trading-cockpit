"""TradeXpress 2.0 Integration Package.

Provides decoupled passive market feed ingestion, order book queue simulation
for SHADOW_DUMMY execution, and preflight safety validation with zero real BDT risk.
"""

from .passive_feed import (
    AccountSummary,
    TradeXpressPassiveFeed,
    get_global_passive_feed,
    get_feed_health_and_guidance,
    ingest_passive_snapshot,
    parse_account_summary_dict,
    parse_ember_market_watch_rows,
    parse_ember_portfolio_rows,
)
from .shadow_simulator import TradeXpressShadowSimulator
from .cdp_daemon import TradeXpressPassiveDaemon, get_global_passive_daemon

__all__ = [
    "AccountSummary",
    "TradeXpressPassiveFeed",
    "get_global_passive_feed",
    "get_feed_health_and_guidance",
    "ingest_passive_snapshot",
    "parse_account_summary_dict",
    "parse_ember_market_watch_rows",
    "parse_ember_portfolio_rows",
    "TradeXpressShadowSimulator",
    "TradeXpressPassiveDaemon",
    "get_global_passive_daemon",
]
