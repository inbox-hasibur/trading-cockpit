"""Schemas for Humming Bird Hermes Plugin tools."""

from __future__ import annotations

HB_PORTFOLIO_SCHEMA = {
    "name": "hb_portfolio",
    "description": "Fetch current portfolio state including cash balance, equity value, unrealized PnL, and active holdings.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

HB_WATCHLIST_SCHEMA = {
    "name": "hb_watchlist",
    "description": "Fetch Humming Bird watchlist and tiered candidates (e.g. GSC, GSC_L1, GSC_L2).",
    "parameters": {
        "type": "object",
        "properties": {
            "tier": {
                "type": "string",
                "description": "Optional tier filter: 'GSC', 'GSC_L1', or 'GSC_L2'.",
            },
        },
        "additionalProperties": False,
    },
}

HB_INSPECT_CURVE_SCHEMA = {
    "name": "hb_inspect_curve",
    "description": "Inspect historical price curve, support floor, resistance ceiling, trend metrics, and sparkline points for a specific DSE ticker symbol.",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "DSE stock ticker symbol (e.g. 'BANKASIA', 'GP', 'SQURPHARMA').",
            },
        },
        "required": ["symbol"],
        "additionalProperties": False,
    },
}

HB_MARKET_OPEN_SCHEMA = {
    "name": "hb_market_open",
    "description": "Check whether Dhaka Stock Exchange (DSE) market is currently open according to Asia/Dhaka schedule and holidays.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

HB_CANARIES_SCHEMA = {
    "name": "hb_canaries",
    "description": "Retrieve active 10% canary probe theses, entry prices, target prices, and stop loss levels.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

HB_LOTS_SCHEMA = {
    "name": "hb_lots",
    "description": "Fetch all active tax lots and their T+2 settlement maturity status.",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "Optional ticker symbol filter (e.g. 'BANKASIA').",
            },
        },
        "additionalProperties": False,
    },
}

# --- WRITE Tool Schemas ---

HB_SET_TIER_SCHEMA = {
    "name": "hb_set_tier",
    "description": "Set watchlist tier for a DSE stock (e.g. 'GSC', 'GSC_L1', 'GSC_L2').",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "DSE stock ticker symbol (e.g. 'BANKASIA').",
            },
            "tier": {
                "type": "string",
                "description": "Watchlist tier category ('GSC', 'GSC_L1', or 'GSC_L2').",
            },
        },
        "required": ["symbol", "tier"],
        "additionalProperties": False,
    },
}

HB_SET_ALLOCATION_SCHEMA = {
    "name": "hb_set_allocation",
    "description": "Set target buy allocation percentage (0 to 100) for a DSE stock.",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "DSE stock ticker symbol (e.g. 'BANKASIA').",
            },
            "buy_allocation_pct": {
                "type": "number",
                "description": "Target buy allocation percentage (0 to 100).",
            },
            "enabled": {
                "type": "boolean",
                "description": "Whether this allocation rule is active.",
            },
        },
        "required": ["symbol", "buy_allocation_pct"],
        "additionalProperties": False,
    },
}

HB_QUARANTINE_CANARY_SCHEMA = {
    "name": "hb_quarantine_canary",
    "description": "Trigger emergency crash quarantine for a company, immediately liquidating 90% and reserving 10% for a Canary probe thesis.",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "DSE stock ticker symbol to quarantine (e.g. 'GP').",
            },
            "reason": {
                "type": "string",
                "description": "Reason for triggering emergency crash quarantine.",
            },
        },
        "required": ["symbol"],
        "additionalProperties": False,
    },
}

HB_RESTORE_QUARANTINE_SCHEMA = {
    "name": "hb_restore_quarantine",
    "description": "Restore a company from crash quarantine back into active trading status.",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "DSE stock ticker symbol to restore.",
            },
            "reason": {
                "type": "string",
                "description": "Reason or justification for restoring the company.",
            },
        },
        "required": ["symbol"],
        "additionalProperties": False,
    },
}

HB_SYNC_SCHEMA = {
    "name": "hb_sync",
    "description": "Trigger synchronization with StockNow data (target: 'portfolio', 'favorites', or 'all_shares').",
    "parameters": {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "enum": ["portfolio", "favorites", "all_shares"],
                "description": "Synchronization target.",
            },
        },
        "required": ["target"],
        "additionalProperties": False,
    },
}

HB_PLACE_ORDER_SCHEMA = {
    "name": "hb_place_order",
    "description": "Submit a virtual BUY or SELL order. dry_run=true by default for safe pre-trade simulation. Real execution requires dry_run=false AND confirm=true.",
    "parameters": {
        "type": "object",
        "properties": {
            "symbol": {
                "type": "string",
                "description": "DSE stock ticker symbol (e.g. 'BANKASIA').",
            },
            "side": {
                "type": "string",
                "enum": ["BUY", "SELL"],
                "description": "Order side: 'BUY' or 'SELL'.",
            },
            "quantity": {
                "type": "integer",
                "description": "Number of shares to trade (positive integer).",
            },
            "price": {
                "type": "number",
                "description": "Optional unit limit price. Defaults to last market price if omitted.",
            },
            "dry_run": {
                "type": "boolean",
                "description": "Safe simulation mode (default: true). Must explicitly pass false for real execution.",
            },
            "confirm": {
                "type": "boolean",
                "description": "Explicit confirmation flag required when dry_run=false for real live submission.",
            },
            "portfolio_id": {
                "type": "string",
                "description": "Target portfolio ID (must be '164580').",
            },
            "idempotency_key": {
                "type": "string",
                "description": "Unique idempotency key to prevent double execution.",
            },
        },
        "required": ["symbol", "side", "quantity"],
        "additionalProperties": False,
    },
}

HB_ROLLBACK_LAST_SCHEMA = {
    "name": "hb_rollback_last",
    "description": "Roll back the most recent state checkpoint atomically across ledger, holdings, and allocations.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}
