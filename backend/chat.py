"""Hermes Agentic Share Assistant and Autonomous Orchestrator.

Hermes is not merely a read-only chat; it acts as a human-like intelligent
trading assistant capable of executing user-directed thesis actions:
- Emergency Crash Quarantine with 90% profit lock + 10% canary observation probe
- Automatic thesis follow-up reporting (confirming collapse or validating stability)
- Quarantine restoration and explicit buy/sell commands
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool

from backend.config import DHAKA, Settings
from backend.database import CanaryThesis, ChatBudget, CompanyProfile, CustomRule, Database, PortfolioState, portfolio_state
from backend.engine.agent_actions import (
    check_canary_theses,
    emergency_quarantine_and_canary,
    execute_agentic_buy,
    restore_quarantine,
)
from backend.portfolio import build_snapshot

logger = logging.getLogger(__name__)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

SYSTEM_PROMPT = """You are Hermes, Humming Bird's Agentic Share Assistant and Autonomous Portfolio Co-Pilot for the Bangladesh Stock Market (DSE).
You act as an intelligent, disciplined, human-like share expert.
Respond in the user's language (Bangla, Banglish, or English), clearly and constructively.
All supplied prices, companies' scenarios, fills and performance are SYNTHETIC DEMO data. Always state this when discussing status.
You have executive authority to advise on rules, track user market intelligence (such as impending company insolvency or loss news),
quarantine compromised stocks, execute emergency profit locks with 10% canary probes, and report whether user hypotheses proved true.
The following JSON is the current application snapshot for this request:
"""


class ChatTurn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=8)
    conversation_id: str | None = None

    @field_validator("message")
    @classmethod
    def nonempty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be blank.")
        return value


def match_symbol(text: str, companies: list[dict]) -> dict | None:
    text_lower = text.lower()
    symbol_aliases = {
        "BANKASIA": ["bankasia", "bank asia", "bank-asia"],
        "EXIM1STMF": ["exim1stmf", "exim", "exim 1st", "exim mutual fund"],
        "SQURPHARMA": ["squrpharma", "square pharma", "square pharmaceuticals", "square"],
        "BXPHARMA": ["bxpharma", "beximco pharma", "beximco pharmaceuticals", "beximco"],
        "GP": ["gp", "grameenphone", "grameen phone", "grameen"],
    }
    for company in companies:
        sym = company["symbol"]
        aliases = symbol_aliases.get(sym, [sym.lower()])
        for alias in aliases:
            if alias in text_lower:
                return company
    return None


def format_canary_updates(snapshot: dict) -> str:
    theses = snapshot.get("canary_theses", [])
    notices = []
    for t in theses:
        if t["status"] == "CONFIRMED_LOSS":
            notices.append(
                f"🚨 [Thesis Alert · {t['symbol']}]: আপনি যে সতর্কতা দিয়েছিলেন তা প্রমাণিত হয়েছে—কোম্পানিটির শেয়ারের দাম "
                f"৳{t['entry_price']} থেকে নেমে ৳{t['last_price_observed']} হয়েছে। আমরা সঠিক সময়ে ৯০% বিক্রি করে বড় ক্ষতির হাত থেকে ক্যাপিটাল রক্ষা করেছি!"
            )
        elif t["status"] == "FALSE_ALARM_STABLE":
            notices.append(
                f"ℹ️ [Thesis Update · {t['symbol']}]: আপনি যে সতর্কতার প্রেক্ষিতে পর্যবেক্ষণ করতে বলেছিলেন, "
                f"বিগত {t['observations_count']} সেশনে শেয়ারের দাম ৳{t['last_price_observed']}-এ শক্ত অবস্থানে রয়েছে। কোম্পানিটি এখনো ভালো আছে; "
                f"আপনি চাইলে অনুমতি দিতে পারেন, আমরা একে কোয়ারেন্টাইন থেকে রিস্টোর করতে পারি।"
            )
    return ("\n\n".join(notices) + "\n\n") if notices else ""


def local_summary(message: str, snapshot: dict) -> str:
    metrics = snapshot["metrics"]
    text = message.lower()
    bangla = any("\u0980" <= char <= "\u09ff" for char in text)
    banglish = any(word in text for word in ("koto", "kemon", "obostha", "kon ", "kena", "bikri", "ache"))
    prefix = "DEMO/PAPER · " + snapshot["app"]["date"]
    proactive_notice = format_canary_updates(snapshot)

    symbol = match_symbol(text, snapshot["companies"])
    if symbol:
        company = symbol
        support_pos = company["curve"].get("support_position")
        if not support_pos:
            price_val = float(company["price"])
            sup_val = float(company["curve"].get("support") or company["curve"].get("low") or 0)
            if price_val < sup_val:
                support_pos = f"below support (৳{sup_val:,.2f})"
            elif sup_val > 0 and abs(price_val - sup_val) / sup_val <= 0.002:
                support_pos = f"at support (৳{sup_val:,.2f})"
            elif sup_val > 0 and 0 < (price_val - sup_val) / sup_val <= 0.01:
                support_pos = f"near support (৳{sup_val:,.2f})"
            else:
                support_pos = f"above support (৳{sup_val:,.2f})"

        status_text = (
            f"Status: Quarantined ({company['curve'].get('drawdown_summary') or company['quarantine_reason'] or company['curve']['reason']})."
            if company["quarantined"]
            else "Status: Active."
        )
        return (
            f"{prefix}\n{proactive_notice}{company['symbol']} ({company.get('watchlist_category', 'GSC')}): "
            f"synthetic price ৳{company['price']:,.2f} ({support_pos}); "
            f"{company['holding_qty']} shares ({company['mature_qty']} mature, {company['locked_qty']} locked).\n"
            f"Estimated net P/L: ৳{company['unrealized_pnl']:+,.2f} ({company['net_return_pct']:+.2f}%).\n"
            f"Signal: {company['curve']['signal']}. {company['curve']['reason']}\n"
            f"{status_text}\n"
            "DEMO mode: Hermes Agentic Orchestrator standing by for instructions."
        )
    if any(word in text for word in ("crash", "quarantine", "guard", "safe", "সেফ", "ক্র্যাশ")):
        blocked_list = []
        for c in snapshot["companies"]:
            if c["quarantined"]:
                dd = c["curve"].get("drawdown_summary")
                blocked_list.append(f"{c['symbol']} ({dd})" if dd else c["symbol"])
        blocked = ", ".join(blocked_list) or "none"
        return (
            f"{prefix}\n{proactive_notice}Crash Quarantine status: {blocked}.\n"
            "New buys are strictly blocked on quarantined stocks. "
            "You can command me to quarantine any company with emergency 90% profit lock, "
            "or instruct me to restore a company once verified safe."
        )
    if any(word in text for word in ("matur", "settle", "t+2", "bikri", "বিক্রি", "ম্যাচিউর")):
        holdings = "; ".join(
            f"{company['symbol']} {company['mature_qty']}"
            for company in snapshot["companies"] if company["mature_qty"]
        ) or "none"
        return (
            f"{prefix}\n{proactive_notice}Mature shares: {holdings}. Locked: {metrics['locked_shares']} shares.\n"
            "Matured lots sell sequentially at +1.5%, +3.5%, +6.0% tiers. "
            "Under the Strict No-Loss Rule, we never panic-sell at a loss."
        )
    if any(word in text for word in ("buy", "kena", "কেনা", "allocation")):
        candidates = ", ".join(
            company["symbol"] for company in snapshot["companies"]
            if company["curve"]["signal"] == "BUY_ZONE" and not company["quarantined"]
            and company["rule"]["enabled"]
        ) or "none"
        return (
            f"{prefix}\n{proactive_notice}Heuristic BUY_ZONE: {candidates}.\n"
            "System buys automatically during cycles. You can also explicitly instruct me: 'Buy GP' or 'Set allocation'."
        )
    if bangla:
        return (
            f"{prefix}\n{proactive_notice}এটি সিন্থেটিক ডেটার পেপার-পোর্টফোলিও (DEMO)।\n"
            f"নেট লিকুইডেশন ইকুইটি: ৳{metrics['net_liquidation_equity']:,.2f}\n"
            f"ব্যবহারযোগ্য ক্যাশ: ৳{metrics['available_cash']:,.2f}; আনসেটলড: ৳{metrics['unsettled_proceeds']:,.2f}\n"
            f"নেট realized লাভ: ৳{metrics['realized_pnl']:+,.2f}; আনুমানিক unrealized: ৳{metrics['unrealized_pnl']:+,.2f}\n"
            f"ম্যাচিউর শেয়ার: {metrics['mature_shares']}; লকড: {metrics['locked_shares']}।\n"
            "আমি হার্মিস (Hermes), আপনার এজেনটিক ট্রেডিং অ্যাসিস্ট্যান্ট। যেকোনো নির্দেশনায় প্রস্তুত।"
        )
    if banglish:
        return (
            f"{prefix}\n{proactive_notice}Eta synthetic paper portfolio (DEMO).\n"
            f"Net liquidation equity ৳{metrics['net_liquidation_equity']:,.2f}; "
            f"available cash ৳{metrics['available_cash']:,.2f}.\n"
            f"Realized net gain ৳{metrics['realized_pnl']:+,.2f}; "
            f"unrealized: ৳{metrics['unrealized_pnl']:+,.2f}.\n"
            f"Mature {metrics['mature_shares']} shares, locked {metrics['locked_shares']}; "
            f"quarantine {metrics['quarantined_count']} company.\n"
            "Ami Hermes, apnar agentic trading assistant. Kono company crash alert ba buy/sell bolte paren."
        )
    return (
        f"{prefix}\n{proactive_notice}Net liquidation equity: ৳{metrics['net_liquidation_equity']:,.2f}\n"
        f"Available cash: ৳{metrics['available_cash']:,.2f}; unsettled proceeds: ৳{metrics['unsettled_proceeds']:,.2f}\n"
        f"Realized net P/L: ৳{metrics['realized_pnl']:+,.2f}; "
        f"estimated unrealized net P/L: ৳{metrics['unrealized_pnl']:+,.2f}\n"
        f"Mature / locked: {metrics['mature_shares']} / {metrics['locked_shares']} shares.\n"
        "DEMO mode: Hermes Agentic Orchestrator standing by."
    )


class ChatService:
    def __init__(self, database: Database, settings: Settings, stocknow_client: Any | None = None):
        self.database = database
        self.settings = settings
        self.stocknow_client = stocknow_client
        self.transport: httpx.AsyncBaseTransport | None = None  # Injectable mock for network-free tests.
        from backend.hermes.agent_loop import HermesAgentLoop
        self.agent_loop = HermesAgentLoop(database, settings, stocknow_client=stocknow_client)

    async def respond(self, request: ChatRequest) -> dict:
        self.agent_loop.transport = self.transport
        res = await self.agent_loop.run_turn(
            request.message,
            [turn.model_dump() for turn in request.history],
            conversation_id=request.conversation_id,
        )
        if "served_by" not in res:
            prov = (res.get("provider") or "LOCAL").upper()
            tier = 3 if prov == "LOCAL" else (2 if prov == "GEMINI" else 1)
            res["served_by"] = {
                "tier": tier,
                "provider": prov,
                "model": res.get("model") or "hermes-local-quant",
                "fallback_reason": None,
            }
        return res
