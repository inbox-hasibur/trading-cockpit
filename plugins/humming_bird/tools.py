"""Tool handlers for Humming Bird Hermes Plugin."""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)


def _kernel_get(endpoint: str, params: dict[str, Any] | None = None) -> str:
    """Perform authenticated GET request to local Humming Bird kernel API."""
    base_url = (os.getenv("KERNEL_URL") or "http://127.0.0.1:8000").rstrip("/")
    token = os.getenv("KERNEL_TOKEN") or ""

    clean_endpoint = "/" + endpoint.lstrip("/")
    url = f"{base_url}{clean_endpoint}"
    if params:
        clean_params = {k: v for k, v in params.items() if v is not None}
        if clean_params:
            url = f"{url}?{urllib.parse.urlencode(clean_params)}"

    req = urllib.request.Request(
        url,
        headers={
            "X-Kernel-Token": token,
            "Accept": "application/json",
            "User-Agent": "Hermes-HummingBird-Plugin/0.2.0",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
            detail = parsed.get("detail", body)
        except Exception:
            detail = body or e.reason
        return json.dumps({"error": f"HTTP {e.code}: {detail}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def _kernel_post(endpoint: str, data: dict[str, Any] | None = None) -> str:
    """Perform authenticated POST request to local Humming Bird kernel API."""
    base_url = (os.getenv("KERNEL_URL") or "http://127.0.0.1:8000").rstrip("/")
    token = os.getenv("KERNEL_TOKEN") or ""

    clean_endpoint = "/" + endpoint.lstrip("/")
    url = f"{base_url}{clean_endpoint}"

    encoded_data = json.dumps(data or {}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=encoded_data,
        headers={
            "X-Kernel-Token": token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Hermes-HummingBird-Plugin/0.2.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(body)
            detail = parsed.get("detail", body)
        except Exception:
            detail = body or e.reason
        return json.dumps({"error": f"HTTP {e.code}: {detail}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- READ Tools ---

def hb_portfolio(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Fetch current portfolio state from kernel API."""
    raw = _kernel_get("/k/portfolio")
    try:
        data = json.loads(raw)
        if not isinstance(data, dict) or "metrics" not in data:
            return raw

        holdings = []
        for c in data.get("companies", []):
            if c.get("holding_qty", 0) > 0:
                holdings.append({
                    "symbol": c.get("symbol"),
                    "name": c.get("name"),
                    "sector": c.get("sector"),
                    "holding_qty": c.get("holding_qty"),
                    "mature_qty": c.get("mature_qty"),
                    "locked_qty": c.get("locked_qty"),
                    "cost_basis": c.get("cost_basis"),
                    "estimated_net_value": c.get("estimated_net_value"),
                    "unrealized_pnl": c.get("unrealized_pnl"),
                    "net_return_pct": c.get("net_return_pct"),
                    "quarantined": c.get("quarantined", False),
                })

        summary = {
            "metrics": data.get("metrics"),
            "holdings": holdings,
            "canary_theses": data.get("canary_theses", []),
            "market_clock": data.get("market_clock"),
            "trade_count": data.get("trade_count"),
        }
        return json.dumps(summary, indent=2)
    except Exception:
        return raw


def hb_watchlist(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Fetch watchlist filtered optionally by tier from kernel API."""
    merged = dict(args or {})
    merged.update(kwargs)
    tier = merged.get("tier")
    params = {"tier": tier} if tier else None
    return _kernel_get("/k/watchlist", params)


def hb_inspect_curve(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Inspect price curve and support/resistance analysis for a symbol."""
    merged = dict(args or {})
    merged.update(kwargs)
    symbol = merged.get("symbol")
    if not symbol:
        return json.dumps({"error": "symbol is required"})
    sym = str(symbol).strip().upper()
    return _kernel_get(f"/k/curve/{sym}")


def hb_market_open(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Check if DSE market is currently open."""
    return _kernel_get("/k/market-open")


def hb_canaries(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Retrieve active canary theses from kernel API."""
    return _kernel_get("/k/canaries")


def hb_lots(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Fetch tax lots and T+2 maturity status."""
    merged = dict(args or {})
    merged.update(kwargs)
    symbol = merged.get("symbol")
    params = {"symbol": str(symbol).strip().upper()} if symbol else None
    return _kernel_get("/k/lots", params)


# --- WRITE Tools ---

def hb_set_tier(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Set watchlist tier for a company."""
    merged = dict(args or {})
    merged.update(kwargs)
    symbol = merged.get("symbol")
    tier = merged.get("tier")
    if not symbol:
        return json.dumps({"error": "symbol is required"})
    if not tier:
        return json.dumps({"error": "tier is required"})
    payload = {"symbol": str(symbol).strip().upper(), "tier": str(tier).strip()}
    return _kernel_post("/k/tier", payload)


def hb_set_allocation(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Set buy allocation percentage for a symbol."""
    merged = dict(args or {})
    merged.update(kwargs)
    symbol = merged.get("symbol")
    allocation = merged.get("buy_allocation_pct")
    if not symbol:
        return json.dumps({"error": "symbol is required"})
    if allocation is None:
        return json.dumps({"error": "buy_allocation_pct is required"})
    try:
        pct = float(allocation)
    except (ValueError, TypeError):
        return json.dumps({"error": "buy_allocation_pct must be a valid number"})
    if not (0 <= pct <= 100):
        return json.dumps({"error": "buy_allocation_pct must be between 0 and 100"})

    enabled = bool(merged.get("enabled", True))
    payload = {
        "symbol": str(symbol).strip().upper(),
        "buy_allocation_pct": pct,
        "enabled": enabled,
    }
    return _kernel_post("/k/allocation", payload)


def hb_quarantine_canary(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Trigger emergency crash quarantine (90% liquidation, 10% canary probe)."""
    merged = dict(args or {})
    merged.update(kwargs)
    symbol = merged.get("symbol")
    if not symbol:
        return json.dumps({"error": "symbol is required"})
    reason = str(merged.get("reason") or "Emergency crash quarantine with 90/10 canary split")
    payload = {
        "symbol": str(symbol).strip().upper(),
        "action": "quarantine",
        "reason": reason,
    }
    return _kernel_post("/k/quarantine", payload)


def hb_restore_quarantine(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Restore a company from crash quarantine back into active status."""
    merged = dict(args or {})
    merged.update(kwargs)
    symbol = merged.get("symbol")
    if not symbol:
        return json.dumps({"error": "symbol is required"})
    reason = str(merged.get("reason") or "Restored from crash quarantine")
    payload = {
        "symbol": str(symbol).strip().upper(),
        "action": "restore",
        "reason": reason,
    }
    return _kernel_post("/k/quarantine", payload)


def hb_sync(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Trigger sync with StockNow market data."""
    merged = dict(args or {})
    merged.update(kwargs)
    target = str(merged.get("target") or "").strip().lower()
    if target not in ("portfolio", "favorites", "all_shares"):
        return json.dumps({"error": "target must be 'portfolio', 'favorites', or 'all_shares'"})
    payload = {"target": target}
    return _kernel_post("/k/sync", payload)


def _get_allowed_portfolios() -> tuple[str, ...]:
    live = (os.getenv("STOCKNOW_LIVE_PORTFOLIO_ID") or "164580").strip()
    test = (os.getenv("STOCKNOW_TEST_PORTFOLIO_ID") or "").strip()
    return (live, test) if test else (live,)


def hb_place_order(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Submit virtual BUY or SELL order enforcing constraints and authorization."""
    merged = dict(args or {})
    merged.update(kwargs)

    # 1. Enforce allowlist if portfolio_id is supplied
    allowed = _get_allowed_portfolios()
    raw_pid = merged.get("portfolio_id")
    target_pid: str | None = None
    if raw_pid is not None and str(raw_pid).strip():
        target_pid = str(raw_pid).strip()
        if target_pid not in allowed:
            return json.dumps({
                "error": f"Hard fail: Unauthorized portfolio '{target_pid}'. Authorized target portfolios: {list(allowed)}."
            })

    symbol = merged.get("symbol")
    if not symbol:
        return json.dumps({"error": "symbol is required"})
    sym = str(symbol).strip().upper()

    side = str(merged.get("side") or "").strip().upper()
    if side not in ("BUY", "SELL"):
        return json.dumps({"error": "side must be 'BUY' or 'SELL'"})

    try:
        quantity = int(merged.get("quantity") or 0)
    except (ValueError, TypeError):
        return json.dumps({"error": "quantity must be a positive integer"})
    if quantity <= 0:
        return json.dumps({"error": "quantity must be greater than zero"})

    price = merged.get("price")
    dry_run = merged.get("dry_run", True)
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("true", "1", "yes")

    op_confirmed = merged.get("operator_confirmed")
    if op_confirmed is None:
        op_confirmed = merged.get("confirm", False)
    if isinstance(op_confirmed, str):
        op_confirmed = op_confirmed.lower() in ("true", "1", "yes", "confirm")
    else:
        op_confirmed = bool(op_confirmed)

    preview_token = merged.get("preview_token")

    # Real submit safety check: needs dry_run=false AND explicit operator confirmation
    if not dry_run and not op_confirmed:
        return json.dumps({
            "error": "Real order submission requires explicit operator confirmation (operator_confirmed=true).",
            "requires_confirmation": True,
            "order_preview": {
                "symbol": sym,
                "side": side,
                "quantity": quantity,
                "price": price,
                "portfolio_id": target_pid or allowed[0],
                "dry_run": False,
            },
        })

    idempotency_key = merged.get("idempotency_key")
    if not idempotency_key:
        idempotency_key = f"order-{sym}-{side}-{quantity}-{int(time.time() * 1000)}"

    payload: dict[str, Any] = {
        "idempotency_key": str(idempotency_key),
        "symbol": sym,
        "side": side,
        "quantity": quantity,
        "price": float(price) if price is not None else None,
        "dry_run": dry_run,
        "operator_confirmed": op_confirmed,
    }
    if target_pid:
        payload["portfolio_id"] = target_pid
    if preview_token:
        payload["preview_token"] = str(preview_token).strip()
    return _kernel_post("/k/order", payload)


def hb_rollback_last(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Roll back the last state checkpoint atomically."""
    return _kernel_post("/k/rollback", {})


def hb_automation_get(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Fetch current automation settings from the trading kernel."""
    return _kernel_get("/k/automation")


def hb_automation_set(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Configure trading automation switches, ingestion mode, or polling cadence."""
    merged = dict(args or {})
    merged.update(kwargs)

    payload: dict[str, Any] = {}
    if "automation_enabled" in merged:
        val = merged["automation_enabled"]
        payload["automation_enabled"] = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "yes")
    elif "master_enabled" in merged:
        val = merged["master_enabled"]
        payload["automation_enabled"] = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "yes")

    if "paused" in merged:
        val = merged["paused"]
        payload["paused"] = val if isinstance(val, bool) else str(val).lower() in ("true", "1", "yes")

    if "ingestion_mode" in merged and merged["ingestion_mode"]:
        payload["ingestion_mode"] = str(merged["ingestion_mode"]).strip().upper()

    if "polling_interval_sec" in merged and merged["polling_interval_sec"] is not None:
        try:
            payload["polling_interval_sec"] = int(merged["polling_interval_sec"])
        except (ValueError, TypeError):
            return json.dumps({"error": "polling_interval_sec must be an integer"})

    if not payload:
        return json.dumps({"error": "At least one automation field must be specified to update."})

    return _kernel_post("/k/automation", payload)


def hb_scheduler(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Control or inspect the market scheduler background loop."""
    merged = dict(args or {})
    merged.update(kwargs)

    action = str(merged.get("action") or "").strip().lower()
    if action not in ("start", "stop", "status"):
        return json.dumps({"error": "action must be 'start', 'stop', or 'status'"})

    return _kernel_post("/k/scheduler", {"action": action})


def hb_run_cycle(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Trigger an immediate AutoTrader cycle."""
    merged = dict(args or {})
    merged.update(kwargs)

    dry_run = merged.get("dry_run", True)
    if isinstance(dry_run, str):
        dry_run = dry_run.lower() in ("true", "1", "yes")

    payload: dict[str, Any] = {"dry_run": dry_run}
    if "idempotency_key" in merged and merged["idempotency_key"]:
        payload["idempotency_key"] = str(merged["idempotency_key"])

    return _kernel_post("/k/cycle", payload)


def hb_stocknow_session(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Manage live Playwright session for StockNow integration."""
    merged = dict(args or {})
    merged.update(kwargs)

    action = str(merged.get("action") or "").strip().lower()
    if action not in ("launch", "status", "login"):
        return json.dumps({"error": "action must be 'launch', 'status', or 'login'"})

    payload: dict[str, Any] = {"action": action}
    if "mode" in merged and merged["mode"]:
        payload["mode"] = str(merged["mode"]).strip().upper()

    return _kernel_post("/k/stocknow/session", payload)


def hb_mode_get(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Get active trading mode from kernel."""
    return _kernel_get("/k/mode")


def hb_mode_set(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Set trading mode in kernel (TEST_OFFHOURS or LIVE_HOURS)."""
    merged = dict(args or {})
    merged.update(kwargs)

    mode = str(merged.get("trading_mode") or "").strip().upper()
    if mode not in ("TEST_OFFHOURS", "LIVE_HOURS"):
        return json.dumps({"error": f"Invalid trading_mode '{mode}'. Allowed values: TEST_OFFHOURS, LIVE_HOURS."})

    confirm = bool(merged.get("confirm", False))
    if mode == "TEST_OFFHOURS" and not confirm:
        return json.dumps({
            "error": "Switching to TEST_OFFHOURS bypasses DSE market hours and requires operator confirmation. Please ask the operator for explicit confirmation before calling with confirm=true."
        })

    payload = {"trading_mode": mode, "confirm": confirm}
    return _kernel_post("/k/mode", payload)


def hb_caps_get(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Get active risk caps and daily limits from kernel."""
    return _kernel_get("/k/caps")


def hb_caps_set(args: dict[str, Any] | None = None, **kwargs) -> str:
    """Set or lower risk limits in kernel. Raising a limit requires confirm=true."""
    merged = dict(args or {})
    merged.update(kwargs)

    payload: dict[str, Any] = {}
    if "max_order_bdt" in merged and merged["max_order_bdt"] is not None:
        try:
            payload["max_order_bdt"] = float(merged["max_order_bdt"])
        except (ValueError, TypeError):
            return json.dumps({"error": "max_order_bdt must be a number"})
    if "max_symbol_bdt" in merged and merged["max_symbol_bdt"] is not None:
        try:
            payload["max_symbol_bdt"] = float(merged["max_symbol_bdt"])
        except (ValueError, TypeError):
            return json.dumps({"error": "max_symbol_bdt must be a number"})
    if "daily_budget_bdt" in merged and merged["daily_budget_bdt"] is not None:
        try:
            payload["daily_budget_bdt"] = float(merged["daily_budget_bdt"])
        except (ValueError, TypeError):
            return json.dumps({"error": "daily_budget_bdt must be a number"})
    if "max_orders_per_day" in merged and merged["max_orders_per_day"] is not None:
        try:
            payload["max_orders_per_day"] = int(merged["max_orders_per_day"])
        except (ValueError, TypeError):
            return json.dumps({"error": "max_orders_per_day must be an integer"})
    if "kill_switch_active" in merged and merged["kill_switch_active"] is not None:
        val = merged["kill_switch_active"]
        if isinstance(val, str):
            val = val.lower() in ("true", "1", "yes")
        payload["kill_switch_active"] = bool(val)

    confirm = merged.get("confirm", False)
    if isinstance(confirm, str):
        confirm = confirm.lower() in ("true", "1", "yes", "confirm")
    payload["confirm"] = bool(confirm)

    return _kernel_post("/k/caps", payload)


