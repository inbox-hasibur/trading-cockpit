"""Humming Bird Plugin for Nous Research Hermes Agent."""

from __future__ import annotations

from pathlib import Path

from .hooks import on_pre_tool_call
from .schemas import (
    HB_CANARIES_SCHEMA,
    HB_INSPECT_CURVE_SCHEMA,
    HB_LOTS_SCHEMA,
    HB_MARKET_OPEN_SCHEMA,
    HB_PLACE_ORDER_SCHEMA,
    HB_PORTFOLIO_SCHEMA,
    HB_QUARANTINE_CANARY_SCHEMA,
    HB_RESTORE_QUARANTINE_SCHEMA,
    HB_ROLLBACK_LAST_SCHEMA,
    HB_SET_ALLOCATION_SCHEMA,
    HB_SET_TIER_SCHEMA,
    HB_SYNC_SCHEMA,
    HB_WATCHLIST_SCHEMA,
)
from .tools import (
    hb_canaries,
    hb_inspect_curve,
    hb_lots,
    hb_market_open,
    hb_place_order,
    hb_portfolio,
    hb_quarantine_canary,
    hb_restore_quarantine,
    hb_rollback_last,
    hb_set_allocation,
    hb_set_tier,
    hb_sync,
    hb_watchlist,
)

_TOOLS = (
    ("hb_portfolio", HB_PORTFOLIO_SCHEMA, hb_portfolio),
    ("hb_watchlist", HB_WATCHLIST_SCHEMA, hb_watchlist),
    ("hb_inspect_curve", HB_INSPECT_CURVE_SCHEMA, hb_inspect_curve),
    ("hb_market_open", HB_MARKET_OPEN_SCHEMA, hb_market_open),
    ("hb_canaries", HB_CANARIES_SCHEMA, hb_canaries),
    ("hb_lots", HB_LOTS_SCHEMA, hb_lots),
    ("hb_set_tier", HB_SET_TIER_SCHEMA, hb_set_tier),
    ("hb_set_allocation", HB_SET_ALLOCATION_SCHEMA, hb_set_allocation),
    ("hb_quarantine_canary", HB_QUARANTINE_CANARY_SCHEMA, hb_quarantine_canary),
    ("hb_restore_quarantine", HB_RESTORE_QUARANTINE_SCHEMA, hb_restore_quarantine),
    ("hb_sync", HB_SYNC_SCHEMA, hb_sync),
    ("hb_place_order", HB_PLACE_ORDER_SCHEMA, hb_place_order),
    ("hb_rollback_last", HB_ROLLBACK_LAST_SCHEMA, hb_rollback_last),
)


def register(ctx) -> None:
    """Register Humming Bird trading kernel tools and lifecycle hooks with Hermes."""
    for name, schema, handler in _TOOLS:
        ctx.register_tool(
            name=name,
            toolset="humming_bird",
            schema=schema,
            handler=handler,
        )

    # Register pre-tool-call lifecycle hook to enforce market hours & approvals
    ctx.register_hook("pre_tool_call", on_pre_tool_call)

    # Register procedural skills
    skills_dir = Path(__file__).parent / "skills"
    if skills_dir.exists():
        for skill_dir in sorted(skills_dir.iterdir()):
            skill_md = skill_dir / "SKILL.md"
            if skill_md.is_file():
                description = ""
                fm = {}
                try:
                    content = skill_md.read_text(encoding="utf-8")
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            for line in parts[1].splitlines():
                                if ":" in line:
                                    k, v = line.split(":", 1)
                                    fm[k.strip()] = v.strip().strip('"').strip("'")
                            description = fm.get("description", "")
                except Exception:
                    pass
                ctx.register_skill(
                    name=skill_dir.name,
                    path=skill_md,
                    description=description,
                    frontmatter=fm,
                )

