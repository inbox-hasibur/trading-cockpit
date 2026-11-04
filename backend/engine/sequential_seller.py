"""Pure, persistent-state-friendly fee-inclusive sequential selling decisions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from decimal import Decimal

from backend.engine.money import HUNDRED, ZERO, allocated_basis, sale_amount, whole_shares


@dataclass(frozen=True)
class SellState:
    remaining_qty: int
    remaining_basis: Decimal
    matures_on: date
    cycle_base_qty: int
    peak_price: Decimal
    next_tier: int = 0
    phase: str = "ACTIVE"
    recovery_anchor: Decimal | None = None


@dataclass(frozen=True)
class SellPlan:
    action: str
    reason: str
    state: SellState
    quantity: int = 0
    cost_basis: Decimal = ZERO
    proceeds: Decimal = ZERO
    fee: Decimal = ZERO
    realized_pnl: Decimal = ZERO
    net_return_pct: Decimal = ZERO


def plan_sale(
    state: SellState,
    *,
    current_price: Decimal,
    as_of: date,
    sell_fee_rate: Decimal = Decimal("0.005"),
    tiers: tuple[Decimal, ...] = (Decimal("1.5"), Decimal("3.5"), Decimal("6.0")),
    slices: tuple[Decimal, ...] = (Decimal("25"), Decimal("25"), Decimal("25")),
    pullback_pct: Decimal = Decimal("3"),
) -> SellPlan:
    if (
        len(tiers) != len(slices)
        or not tiers
        or any(tier <= 0 for tier in tiers)
        or any(a >= b for a, b in zip(tiers, tiers[1:]))
        or any(not ZERO < portion <= HUNDRED for portion in slices)
        or sum(slices) > HUNDRED
        or not ZERO < pullback_pct < HUNDRED
    ):
        raise ValueError("Invalid profit tier, slice, or pullback rule.")
    if not current_price.is_finite() or current_price <= ZERO:
        raise ValueError("Sale price must be finite and positive.")
    if state.remaining_qty <= 0:
        return SellPlan("CLOSED", "No remaining shares.", state)
    if state.remaining_basis <= ZERO or state.cycle_base_qty <= 0:
        raise ValueError("Open lots require positive remaining cost basis and cycle quantity.")
    if state.matures_on > as_of:
        return SellPlan("SETTLEMENT_LOCK", f"Lot matures on {state.matures_on.isoformat()}.", state)

    state = replace(state, peak_price=max(state.peak_price, current_price))
    estimated_proceeds, _ = sale_amount(state.remaining_qty, current_price, sell_fee_rate)
    net_return = (estimated_proceeds / state.remaining_basis - 1) * HUNDRED
    if estimated_proceeds <= state.remaining_basis:
        return SellPlan(
            "NO_LOSS_HOLD",
            f"Estimated exit is {net_return:.2f}% net; strict no-loss policy holds (loss still exists).",
            state,
            net_return_pct=net_return,
        )

    if state.phase == "RECOVERY_HOLD":
        if state.recovery_anchor is None or current_price < state.recovery_anchor:
            anchor = f"{state.recovery_anchor:.4f}" if state.recovery_anchor else "unavailable"
            return SellPlan(
                "RECOVERY_HOLD",
                f"Retained half waits for saved peak {anchor}; do not repeatedly halve it.",
                state,
                net_return_pct=net_return,
            )
        state = replace(
            state,
            phase="ACTIVE",
            cycle_base_qty=state.remaining_qty,
            next_tier=0,
            peak_price=current_price,
            recovery_anchor=None,
        )
    elif state.phase != "ACTIVE":
        raise ValueError("Unknown selling phase for an open lot.")

    drawdown = (1 - current_price / state.peak_price) * HUNDRED
    if drawdown >= pullback_pct:
        quantity = state.remaining_qty // 2
        if quantity == 0:
            return SellPlan(
                "HOLD_ODD_SHARE", "One share cannot be split into two halves; retain it.", state,
                net_return_pct=net_return,
            )
        action = "PULLBACK_SPLIT"
        reason = (
            f"{drawdown:.2f}% pullback while net profitable: sell half, retain half for recovery."
        )
        updated = replace(state, phase="RECOVERY_HOLD", recovery_anchor=state.peak_price)
    elif state.next_tier < len(tiers) and net_return >= tiers[state.next_tier]:
        quantity = min(
            state.remaining_qty,
            max(1, whole_shares(Decimal(state.cycle_base_qty) * slices[state.next_tier] / HUNDRED)),
        )
        action = f"SELL_TIER_{state.next_tier + 1}"
        reason = (
            f"Net {net_return:.2f}% crosses tier {state.next_tier + 1} "
            f"(+{tiers[state.next_tier]}%); sell a cycle-base slice, not everything."
        )
        updated = replace(state, next_tier=state.next_tier + 1)
    else:
        action = "HOLD_RUNNER" if state.next_tier >= len(tiers) else "HOLD_TIER"
        return SellPlan(action, "Keep remaining shares; no new profitable tier/pullback.", state,
                        net_return_pct=net_return)

    cost_basis = allocated_basis(state.remaining_basis, state.remaining_qty, quantity)
    proceeds, fee = sale_amount(quantity, current_price, sell_fee_rate)
    pnl = proceeds - cost_basis
    if pnl <= ZERO:
        return SellPlan(
            "WAIT_FEE_ROUNDING", "This whole-share slice is not profitable after money rounding.",
            state, net_return_pct=net_return,
        )
    updated = replace(
        updated,
        remaining_qty=state.remaining_qty - quantity,
        remaining_basis=state.remaining_basis - cost_basis,
    )
    if updated.remaining_qty == 0:
        updated = replace(updated, phase="CLOSED", recovery_anchor=None)
    return SellPlan(action, reason, updated, quantity, cost_basis, proceeds, fee, pnl, net_return)
