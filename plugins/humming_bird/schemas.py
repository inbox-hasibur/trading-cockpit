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
    "description": "Submit a virtual BUY or SELL order. dry_run=true by default for safe pre-trade simulation. Real execution requires dry_run=false AND operator_confirmed=true.",
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
            "operator_confirmed": {
                "type": "boolean",
                "description": "Explicit operator confirmation flag required when dry_run=false. Must only be true if operator explicitly commanded this order.",
            },
            "confirm": {
                "type": "boolean",
                "description": "Alias for operator_confirmed.",
            },
            "preview_token": {
                "type": "string",
                "description": "Preview token from prior dry_run preview. Required for two-step confirmation in LIVE_HOURS mode.",
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

HB_AUTOMATION_GET_SCHEMA = {
    "name": "hb_automation_get",
    "description": "Fetch master buy/sell automation switch status, engine paused state, ingestion mode, and polling cadence.",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

HB_AUTOMATION_SET_SCHEMA = {
    "name": "hb_automation_set",
    "description": "Configure trading automation settings: toggle master buy/sell automation on/off, pause/resume engine, set ingestion mode ('BACKGROUND_POLLING' or 'ONSCREEN_LIVE'), or adjust polling interval (seconds).",
    "parameters": {
        "type": "object",
        "properties": {
            "automation_enabled": {
                "type": "boolean",
                "description": "Enable (true) or disable (false) master automated trading.",
            },
            "paused": {
                "type": "boolean",
                "description": "Pause (true) or unpause (false) the trading execution engine.",
            },
            "ingestion_mode": {
                "type": "string",
                "enum": ["BACKGROUND_POLLING", "ONSCREEN_LIVE"],
                "description": "Market data ingestion mode: 'BACKGROUND_POLLING' or 'ONSCREEN_LIVE'.",
            },
            "polling_interval_sec": {
                "type": "integer",
                "description": "Polling frequency in seconds (e.g. 60, 120, 300).",
            },
        },
        "additionalProperties": False,
    },
}

HB_SCHEDULER_SCHEMA = {
    "name": "hb_scheduler",
    "description": "Control or inspect the background market scheduler loop. Action must be 'start', 'stop', or 'status'.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start", "stop", "status"],
                "description": "Scheduler action to execute: 'start', 'stop', or 'status'.",
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    },
}

HB_RUN_CYCLE_SCHEMA = {
    "name": "hb_run_cycle",
    "description": "Execute an immediate evaluation cycle through AutoTrader. dry_run=true by default for safe evaluation.",
    "parameters": {
        "type": "object",
        "properties": {
            "dry_run": {
                "type": "boolean",
                "description": "Safe simulation mode (default: true). Set false for live execution.",
            },
            "idempotency_key": {
                "type": "string",
                "description": "Optional idempotency deduplication key.",
            },
        },
        "additionalProperties": False,
    },
}

HB_STOCKNOW_SESSION_SCHEMA = {
    "name": "hb_stocknow_session",
    "description": "Manage live Playwright browser session for StockNow integration. Action must be 'launch', 'status', or 'login'.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["launch", "status", "login"],
                "description": "Session action: 'launch', 'status', or 'login'.",
            },
            "mode": {
                "type": "string",
                "enum": ["ONSCREEN_LIVE", "BACKGROUND_POLLING"],
                "description": "Optional browser display mode when launching: 'ONSCREEN_LIVE' or 'BACKGROUND_POLLING'.",
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    },
}

HB_MODE_GET_SCHEMA = {
    "name": "hb_mode_get",
    "description": "Get current DSE trading mode (TEST_OFFHOURS or LIVE_HOURS).",
    "parameters": {
        "type": "object",
        "properties": {},
        "additionalProperties": False,
    },
}

HB_MODE_SET_SCHEMA = {
    "name": "hb_mode_set",
    "description": "Set DSE trading mode. Values: 'TEST_OFFHOURS' (bypasses market hours gate) or 'LIVE_HOURS' (strictly limits real orders to Sun-Thu 10:00-14:30). Switching to TEST_OFFHOURS strictly requires operator confirmation (confirm=true).",
    "parameters": {
        "type": "object",
        "properties": {
            "trading_mode": {
                "type": "string",
                "enum": ["TEST_OFFHOURS", "LIVE_HOURS"],
                "description": "Trading mode: 'TEST_OFFHOURS' or 'LIVE_HOURS'.",
            },
            "confirm": {
                "type": "boolean",
                "description": "Mandatory operator confirmation boolean when switching to TEST_OFFHOURS.",
            },
        },
        "required": ["trading_mode"],
        "additionalProperties": False,
    },
}

