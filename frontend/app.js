"use strict";

// ==========================================================================
// Project Humming Bird · Core Cockpit Controller & Orchestrator
// State store, API bridge, live stream SSE listener, and table views.
// ==========================================================================

"use strict";

// The browser is a display/control surface, never the source of trading math.
const $ = (id) => document.getElementById(id);
const SVG_NS = "http://www.w3.org/2000/svg";
const numberFormat = new Intl.NumberFormat("en-BD", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const sessionFormat = new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", year: "numeric", timeZone: "Asia/Dhaka" });
const shortDateFormat = new Intl.DateTimeFormat("en-GB", { day: "2-digit", month: "short", timeZone: "Asia/Dhaka" });
const clockFormat = new Intl.DateTimeFormat("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false, timeZone: "Asia/Dhaka" });

const catLabels = {
  GSC: "Big Giant Stable",
  GSC_L1: "Upper Trends L1",
  GSC_L2: "Upper Trends L2",
};

const state = {
  snapshot: null,
  selectedSymbol: "BANKASIA",
  activeSector: null,
  period: "overall",
  category: "ALL",
  theme: "dark",
  deepTimeframe: "7d",
  deepCompany: null,
  simDeltaPct: 0,
  modalSimDeltaPct: 0,
  busy: false,
  chatBusy: false,
  allocationDirty: false,
  fetchSequence: 0,
  history: [],
  lastChatProvider: null,
  token: "",
  toastTimer: null,
};
try { state.token = sessionStorage.getItem("humming-bird-token") || ""; } catch { /* Storage is optional. */ }

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = String(text);
  return node;
}

function svgElement(tag, attributes = {}) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([name, value]) => node.setAttribute(name, String(value)));
  return node;
}

function currency(value, signed = false) {
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  const sign = n < 0 ? "−" : signed ? "+" : "";
  return `${sign}৳${numberFormat.format(Math.abs(n))}`;
}

function percentage(value, signed = true) {
  const n = Number(value);
  return Number.isFinite(n) ? `${n < 0 ? "−" : signed ? "+" : ""}${Math.abs(n).toFixed(2)}%` : "—";
}

function sessionDate(value, short = false) {
  return (short ? shortDateFormat : sessionFormat).format(new Date(`${value}T12:00:00+06:00`));
}

function setText(id, text) {
  const node = $(id);
  if (node) node.textContent = String(text);
}

function setPnl(id, value, asPercentage = false) {
  const node = $(id);
  if (!node) return;
  node.textContent = asPercentage ? percentage(value) : currency(value, true);
  node.classList.toggle("positive", value >= 0);
  node.classList.toggle("negative", value < 0);
}

function tone(action) {
  if (/CRASH|BLOCKED|INVALID|STALE/.test(action)) return "negative";
  if (/BUY_ZONE|^BUY$/.test(action)) return "buy";
  if (/SELL_ZONE|^SELL$|SELL_TIER|RECOVERY|PULLBACK|RUNNER/.test(action)) return "sell";
  if (/WAIT|MID_RANGE|NO_CHURN|BUDGET/.test(action)) return "neutral";
  if (/LOCK|LOSS|DISABLED|ODD/.test(action)) return "amber";
  if (/MATURE/.test(action)) return "positive";
  return "neutral";
}

function badge(action, label) {
  const labels = { CRASH_QUARANTINE: "CRASH GUARD", BUY_ZONE: "BUY ZONE", SELL_ZONE: "SELL ZONE", MID_RANGE: "MID RANGE" };
  const node = element("span", `signal-badge tone-${tone(action)}`, label || labels[action] || action.replaceAll("_", " "));
  node.title = action;
  return node;
}

function notify(message, error = false) {
  clearTimeout(state.toastTimer);
  const toast = $("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.hidden = false;
  state.toastTimer = setTimeout(() => { toast.hidden = true; }, 5500);
}

function showError(message, withToast = true) {
  setText("error-text", message);
  const banner = $("error-banner");
  if (banner) banner.hidden = false;
  if (withToast) notify(message, true);
}

async function api(path, { method = "GET", body, headers = {}, timeout = 35000 } = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const requestHeaders = { Accept: "application/json", ...headers };
  if (body !== undefined) requestHeaders["Content-Type"] = "application/json";
  if (state.token) requestHeaders.Authorization = `Bearer ${state.token}`;
  try {
    const response = await fetch(path, {
      method, headers: requestHeaders, body: body === undefined ? undefined : (typeof body === "string" ? body : JSON.stringify(body)),
      signal: controller.signal, cache: "no-store", credentials: "same-origin",
    });
    let data;
    try { data = await response.json(); } catch { throw new Error(`Server returned HTTP ${response.status} without JSON.`); }
    if (!response.ok) {
      const detail = Array.isArray(data.detail) ? data.detail.map((issue) => issue.msg).join("; ") : data.detail;
      const tokenHelp = response.status === 401 ? " Use the API token control in the header." : "";
      throw new Error(`${detail || `Request failed (HTTP ${response.status})`}${tokenHelp}`);
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("Request timed out. Refresh status before retrying; cycles are deduplicated.");
    throw error;
  } finally { clearTimeout(timer); }
}

function updateControls() {
  const ready = Boolean(state.snapshot);
  $("run-cycle").disabled = !ready || state.busy || state.snapshot.app.paused;
  $("pause-button").disabled = !ready || state.busy;
  const topbarInput = $("topbar-automation-toggle-input");
  if (topbarInput) topbarInput.disabled = !ready || state.busy;
  $("next-session").disabled = !ready || state.busy;
  $("scenario").disabled = state.busy;
  $("save-allocation").disabled = !ready || state.busy;
  $("buy-allocation").disabled = !ready || state.busy;
  $("company-enabled").disabled = !ready || state.busy;
  $("chat-send").disabled = !ready || state.chatBusy;
  document.querySelectorAll("[data-prompt]").forEach((button) => { button.disabled = !ready || state.chatBusy; });
  setText("run-label", state.busy ? "Working…" : "Run automation cycle");
  if (ready) {
    const paused = state.snapshot.app.paused;
    const pauseTitle = paused ? "Resume engine" : "Pause engine";
    const pauseBtn = $("pause-button");
    if (pauseBtn) {
      pauseBtn.title = pauseTitle;
      pauseBtn.setAttribute("aria-label", pauseTitle);
      const pauseLabel = $("pause-label");
      if (pauseLabel) pauseLabel.textContent = pauseTitle;
      pauseBtn.classList.toggle("pause-active", paused);
    }
    setText("engine-state", paused ? "ENGINE PAUSED" : "MANUAL CYCLES");
    $("engine-state").classList.toggle("paused", paused);
    renderAutomationControlBar();
  }
}

async function refresh(quiet = false) {
  const sequence = ++state.fetchSequence;
  try {
    const snapshot = await api("/api/portfolio");
    if (sequence !== state.fetchSequence) return;
    state.snapshot = snapshot;
    $("error-banner").hidden = true;
    renderSnapshot();
  } catch (error) {
    if (sequence === state.fetchSequence) showError(`${quiet ? "Refresh failed; the previous snapshot is still displayed. " : ""}${error.message}`, !quiet);
  } finally { updateControls(); }
}

async function mutate(action) {
  if (state.busy) return;
  state.busy = true;
  state.fetchSequence += 1; // Invalidate a poll that started before this mutation.
  updateControls();
  try { await action(); } catch (error) { showError(error.message); }
  finally { state.busy = false; updateControls(); }
}

function renderSnapshot() {
  document.querySelectorAll(".skeleton-placeholder").forEach((el) => { el.classList.remove("skeleton-placeholder"); });
  const { app, metrics } = state.snapshot;
  setText("demo-date", sessionDate(app.date));
  setText("snapshot-label", `Snapshot ${app.revision} · Rules ${app.rules_revision}`);
  setText("metric-equity", currency(metrics.net_liquidation_equity));
  setText("metric-cash", currency(metrics.available_cash));
  setText("metric-unsettled", currency(metrics.unsettled_proceeds));
  setPnl("metric-realized", metrics.realized_pnl);
  setPnl("metric-unrealized", metrics.unrealized_pnl);
  setText("metric-total-gain", `${currency(metrics.total_gain, true)} (${percentage(metrics.total_gain_pct)})`);
  $("metric-total-gain").classList.toggle("positive", metrics.total_gain >= 0);
  $("metric-total-gain").classList.toggle("negative", metrics.total_gain < 0);
  setText("mature-shares", metrics.mature_shares);
  setText("locked-shares", metrics.locked_shares);
  setText("quarantined-count", metrics.quarantined_count);
  setText("fees-paid", currency(metrics.fees_paid));
  setText("ledger-status", metrics.book_reconciled && metrics.equity_reconciled ? "✓ Ledger reconciled" : "! Reconciliation failed");
  renderBuckets();
  renderMainChart();
  renderWatchlist();
  renderMarketMap();
  renderTopSectorsChart();
  renderAutomationControlBar();
  renderInspector();
  renderDecisions();
  renderCanaryTheses();
  renderHermesSkills();
  renderLedger();
  if (!state.lastChatProvider) {
    setText("chat-provider", state.snapshot.chat.provider === "local" ? "LOCAL SUMMARY · NO API COST" : `OPENROUTER · ${state.snapshot.chat.model}`);
    setText("chat-footer-note", state.snapshot.chat.provider === "local" ? "Local summaries are free. External AI is optional." : "External AI receives your demo portfolio context.");
  }
  if (state.snapshot.chat) {
    const used = state.snapshot.chat.external_calls_today || 0;
    const limit = state.snapshot.chat.daily_call_limit || 30;
    const budgetStr = `${used} / ${limit} calls used`;
    setText("settings-budget-text", budgetStr);
    setText("telemetry-usage-text", budgetStr);
    const quotaBar = $("telemetry-quota-bar");
    if (quotaBar) {
      const pct = Math.min(100, Math.round((used / limit) * 100));
      quotaBar.style.width = `${pct}%`;
    }
  }
  updateControls();
}

function renderBuckets() {
  const cards = state.snapshot.buckets.map((bucket) => {
    const card = element("div", `bucket-card${bucket.active ? " is-active" : ""}`);
    card.title = `Initial cash ${currency(bucket.initial_cash)}; unsettled ${currency(bucket.unsettled_proceeds)}; open cost basis ${currency(bucket.open_cost_basis)}.`;
    const left = element("div", "bucket-left");
    left.append(element("span", "bucket-letter", bucket.name));
    const details = element("div");
    const title = element("div", "bucket-title", `Bucket ${bucket.name}`);
    if (bucket.active) title.append(element("span", "bucket-status", "ACTIVE BUY"));
    details.append(title, element("div", "bucket-meta", `${bucket.mature_shares} mature · ${bucket.locked_shares} locked`));

    const totalCash = (Number(bucket.available_cash) || 0) + (Number(bucket.unsettled_proceeds) || 0);
    const settledPct = totalCash > 0 ? ((Number(bucket.available_cash) || 0) / totalCash) * 100 : 100;
    const lockedPct = Math.max(0, 100 - settledPct);
    const bar = element("div", "bucket-progress-bar");
    bar.title = `Settled: ${currency(bucket.available_cash)} (${settledPct.toFixed(0)}%) · Unsettled: ${currency(bucket.unsettled_proceeds)} (${lockedPct.toFixed(0)}%)`;
    const fillSettled = element("div", "bucket-progress-fill settled");
    fillSettled.style.width = `${settledPct}%`;
    const fillLocked = element("div", "bucket-progress-fill locked");
    fillLocked.style.width = `${lockedPct}%`;
    bar.append(fillSettled, fillLocked);
    details.append(bar);

    left.append(details);
    const value = element("div", "bucket-value", currency(bucket.available_cash));
    value.append(element("span", "bucket-caption", "SETTLED CASH"));
    card.append(left, value);
    return card;
  });
  $("bucket-stack").replaceChildren(...cards);
}

function cell(text, className) { return element("td", className, text); }

function selectCompany(symbol) {
  state.selectedSymbol = symbol;
  state.allocationDirty = false;
  renderWatchlist();
  renderInspector();
}

function renderWatchlist() {
  const query = $("company-search").value.trim().toLowerCase();
  const all = state.snapshot.companies;
  const cat = state.category || "ALL";

  const gscCount = all.filter((c) => (c.watchlist_category || "GSC") === "GSC").length;
  const l1Count = all.filter((c) => c.watchlist_category === "GSC_L1").length;
  const l2Count = all.filter((c) => c.watchlist_category === "GSC_L2").length;
  if ($("cat-all-count")) setText("cat-all-count", all.length);
  if ($("cat-gsc-count")) setText("cat-gsc-count", gscCount);
  if ($("cat-l1-count")) setText("cat-l1-count", l1Count);
  if ($("cat-l2-count")) setText("cat-l2-count", l2Count);

  const companies = all.filter((company) => {
    const matchesQuery = `${company.symbol} ${company.name} ${company.sector}`.toLowerCase().includes(query);
    const matchesCat = cat === "ALL" || (company.watchlist_category || "GSC") === cat;
    return matchesQuery && matchesCat;
  });
  setText("company-count", query || cat !== "ALL" ? `${companies.length}/${all.length}` : all.length);
  const rows = companies.map((company) => {
    const row = element("tr", company.symbol === state.selectedSymbol ? "selected" : "");
    row.dataset.symbol = company.symbol;
    const companyCell = cell();
    const button = element("button", "company-button");
    button.type = "button"; button.setAttribute("aria-label", `Inspect ${company.symbol}`);
    button.append(element("span", `company-icon sector-${company.sector.toLowerCase()}`, company.symbol[0]));
    const name = element("span");
    const symSpan = element("span", "company-symbol", company.symbol);
    const catCode = company.watchlist_category || "GSC";
    symSpan.append(element("span", `cat-tag cat-${catCode.toLowerCase()}`, catLabels[catCode] || catCode));
    name.append(symSpan, element("span", "company-subtitle", company.sector.replaceAll("_", " ").toLowerCase()));
    button.append(name); companyCell.append(button);
    const day = cell(percentage(company.curve.day_change_pct), `align-right ${company.curve.day_change_pct >= 0 ? "positive" : "negative"}`);
    const chart = cell(); chart.append(sparkline(company.history));
    const signal = cell();
    const sigBadge = badge(company.curve.signal);
    if (company.quarantined || company.curve.signal === "CRASH_QUARANTINE") {
      let dropVal = company.curve.drawdown_pct ? company.curve.drawdown_pct.toFixed(2) : "0.00";
      if (company.quarantine_reason) {
        const match = company.quarantine_reason.match(/(\d+(?:\.\d+)?)%/);
        if (match) dropVal = parseFloat(match[1]).toFixed(2);
      }
      const nSessions = company.curve.drawdown_sessions || 5;
      sigBadge.title = `Quarantined: ${dropVal}% drawdown over ${nSessions} sessions`;
      signal.title = sigBadge.title;
    } else {
      signal.title = company.curve.reason;
    }
    signal.append(sigBadge);
    const position = cell(undefined, "align-right position-count");
    position.append(element("span", "", company.holding_qty), element("span", "muted", `/ ${company.mature_qty}`));
    const allocation = cell(`${company.rule.buy_allocation_pct}%`, "align-right allocation-value");
    allocation.title = company.rule.enabled ? "Maximum open cost basis as % of initial capital" : "Automation disabled";
    const actionCell = cell(undefined, "align-center");
    const trendBtn = element("button", "button secondary small-button deep-trend-btn", "Trend ⤢");
    trendBtn.type = "button";
    trendBtn.title = `View ${company.symbol} Deep Trend & Fundamentals`;
    trendBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      openDeepTrendModal(company.symbol);
    });
    actionCell.append(trendBtn);
    row.append(companyCell, cell(numberFormat.format(company.price), "align-right"), day, chart, signal, position, allocation, actionCell);
    row.addEventListener("click", () => selectCompany(company.symbol));
    return row;
  });
  if (!rows.length) { const row = element("tr"); const td = cell("No matching companies in this category.", "loading-cell"); td.colSpan = 8; row.append(td); rows.push(row); }
  $("watchlist-body").replaceChildren(...rows);
}

function renderCanaryTheses() {
  const container = $("canary-section");
  if (!container) return;
  const theses = state.snapshot.canary_theses || [];
  if (!theses.length) {
    container.hidden = true;
    return;
  }
  container.hidden = false;
  setText("canary-count", theses.length);
  const feed = $("canary-feed");
  const entries = theses.map((t) => {
    const entry = element("div", "canary-entry");
    const top = element("div", "canary-top");
    top.append(element("strong", "", t.symbol));
    const statusClass = `status-${t.status.toLowerCase()}`;
    top.append(element("span", `canary-status ${statusClass}`, t.status.replaceAll("_", " ")));
    top.append(element("span", "muted small", sessionDate(t.created_on, true)));

    const body = element("p", "", `Thesis: "${t.thesis}"`);
    const note = element("p", "muted", t.notes);
    const foot = element("div", "canary-foot");
    foot.append(
      element("span", "", `Canary probe: ${t.canary_qty} shares`),
      element("span", "", `Alert price: ৳${numberFormat.format(t.entry_price)}`),
      element("span", "", `Observed: ৳${numberFormat.format(t.last_price_observed)}`),
      element("span", "", `Checks: ${t.observations_count} sessions`)
    );
    entry.append(top, body, note, foot);
    return entry;
  });
  feed.replaceChildren(...entries);
}

function renderInspector() {
  const company = state.snapshot.companies.find((item) => item.symbol === state.selectedSymbol) || state.snapshot.companies[0];
  if (!company) return;
  state.selectedSymbol = company.symbol;
  setText("inspector-symbol", company.symbol);
  setText("inspector-sector", company.sector.replaceAll("_", " "));
  setText("inspector-basis", currency(company.cost_basis));
  setPnl("inspector-pnl", company.unrealized_pnl);
  setPnl("inspector-return", company.net_return_pct, true);
  setText("inspector-reason", company.curve.reason + (company.quarantine_persisted ? " Quarantine persists; a rebound does not clear it." : ""));
  const rows = company.lots.map((lot) => {
    const row = element("tr");
    const id = cell(`#${lot.id} · ${lot.bucket}`);
    id.append(element("span", "lot-date", sessionDate(lot.acquired_on, true)));
    const maturity = cell();
    maturity.append(badge(lot.is_mature ? "MATURE" : "SETTLEMENT_LOCK", lot.is_mature ? "MATURE" : `${lot.sessions_until_mature} SESSION${lot.sessions_until_mature === 1 ? "" : "S"} LEFT`));
    maturity.title = `Acquired T+${lot.age_sessions}; matures ${lot.matures_on}`;
    const selling = cell();
    const label = lot.phase === "RECOVERY_HOLD" ? "RECOVERY HOLD" : lot.next_tier >= company.rule.profit_tiers.length ? "RUNNER" : `NEXT TIER ${lot.next_tier + 1}`;
    selling.append(badge(lot.phase, label));
    selling.title = lot.recovery_anchor ? `Retained half waits for recovery anchor ${currency(lot.recovery_anchor)}` : `Cycle base ${lot.cycle_base_qty} shares; peak ${currency(lot.peak_price)}`;
    row.append(id, cell(lot.remaining_qty, "align-right"), maturity, selling, cell(percentage(lot.net_return_pct), `align-right ${lot.net_return_pct >= 0 ? "positive" : "negative"}`));
    return row;
  });
  if (!rows.length) { const row = element("tr"); const td = cell("No open lots for this company.", "loading-cell"); td.colSpan = 5; row.append(td); rows.push(row); }
  $("lots-body").replaceChildren(...rows);
  $("profit-tiers").replaceChildren(...company.rule.profit_tiers.map((value, i) => element("span", "tier-chip", `+${value}% · ${company.rule.tier_slices[i]}% slice`)));
  setText("pullback-setting", `${company.rule.pullback_pct}% pullback → 50/50`);
  if (!state.allocationDirty) {
    $("buy-allocation").value = company.rule.buy_allocation_pct;
    $("company-enabled").checked = company.rule.enabled;
  }
  updateWhatIfSimulator(company);
}

function renderDecisions() {
  const { latest_cycle: cycle, decisions } = state.snapshot;
  setText("cycle-badge", cycle ? `SNAPSHOT ${cycle.revision} · ${cycle.trades.length} TRADES` : "NO CYCLES YET");
  if (!decisions.length) return;
  const entries = decisions.slice(0, 24).map((decision) => {
    const entry = element("article", "decision-entry");
    const top = element("div", "decision-top");
    top.append(element("strong", "", decision.symbol), badge(decision.action));
    if (decision.quantity) top.append(element("span", "decision-quantity", `${decision.quantity} shares`));
    const time = element("time", "", `#${decision.revision} · ${sessionDate(decision.date, true)}`);
    time.dateTime = decision.date; top.append(time);
    entry.append(top, element("p", "", decision.reason));
    return entry;
  });
  $("decision-feed").replaceChildren(...entries);
}

function renderLedger() {
  const period = state.snapshot.periods[state.period];
  setPnl("period-pnl", period.realized_pnl);
  setText("period-buy", currency(period.buy_turnover));
  setText("period-sell", currency(period.sell_turnover));
  setText("period-trades", `${period.buy_count} buy / ${period.sell_count} sell`);
  document.querySelectorAll("[data-period]").forEach((button) => {
    const active = button.dataset.period === state.period;
    button.classList.toggle("active", active); button.setAttribute("aria-pressed", String(active));
  });
  const trades = state.snapshot.trades.filter((trade) => period.start <= trade.date && trade.date <= period.end);
  const rows = trades.map((trade) => {
    const row = element("tr");
    row.title = trade.reason;
    const company = cell(); company.append(element("span", "trade-symbol", trade.symbol));
    company.append(element("div", "trade-source", trade.source === "DEMO_SEED" ? "DEMO SEED" : "PAPER FILL"));
    const side = cell(); side.append(badge(trade.side));
    const settlement = cell(`${trade.bucket} · ${sessionDate(trade.settles_on, true)}`);
    row.append(cell(sessionDate(trade.date, true)), company, side, cell(trade.quantity, "align-right"), cell(numberFormat.format(trade.price), "align-right"), cell(numberFormat.format(trade.fee), "align-right"), cell(trade.side === "SELL" ? `${trade.realized_pnl >= 0 ? "+" : ""}${numberFormat.format(trade.realized_pnl)}` : "—", `align-right ${trade.side === "SELL" ? (trade.realized_pnl >= 0 ? "positive" : "negative") : "muted"}`), settlement);
    return row;
  });
  if (!rows.length) { const row = element("tr"); const td = cell("No trades in this accounting period.", "loading-cell"); td.colSpan = 8; row.append(td); rows.push(row); }
  $("trades-body").replaceChildren(...rows);
  setText("ledger-range", `${sessionDate(period.start, true)} – ${sessionDate(period.end, true)} · Latest 100 records shown; totals use full ledger.`);
}

$("run-cycle").addEventListener("click", () => mutate(async () => {
  const result = await api("/api/automation/cycle", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } });
  await refresh();
  notify(result.duplicate ? "Snapshot already evaluated — no duplicate trades." : `Paper cycle complete: ${result.buy_count} buy, ${result.sell_count} sell. No external orders.`);
}));

$("pause-button").addEventListener("click", () => mutate(async () => {
  const result = await api("/api/automation/pause", { method: "POST", body: { paused: !state.snapshot.app.paused } });
  await refresh();
  notify(result.paused ? "Automation paused. New paper cycles are blocked." : "Engine resumed. Cycles still require a manual click.");
}));

$("next-session").addEventListener("click", () => mutate(async () => {
  const result = await api("/api/demo/advance", { method: "POST", body: { scenario: $("scenario").value } });
  await refresh();
  notify(`Demo moved to ${sessionDate(result.date)} (${result.scenario.toLowerCase()}). No trades executed; run a cycle to evaluate.`);
}));

$("allocation-form").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!$("allocation-form").reportValidity()) return;
  const symbol = state.selectedSymbol;
  const body = { buy_allocation_pct: $("buy-allocation").valueAsNumber, enabled: $("company-enabled").checked };
  mutate(async () => {
    await api(`/api/companies/${encodeURIComponent(symbol)}/allocation`, { method: "PATCH", body });
    state.allocationDirty = false;
    await refresh();
    notify(`${symbol} settings saved. No trades executed.`);
  });
});
$("buy-allocation").addEventListener("input", () => { state.allocationDirty = true; });
$("company-enabled").addEventListener("change", () => { state.allocationDirty = true; });
$("company-search").addEventListener("input", () => { if (state.snapshot) renderWatchlist(); });
$("dismiss-error").addEventListener("click", () => { $("error-banner").hidden = true; });

document.querySelectorAll("[data-period]").forEach((button) => button.addEventListener("click", () => {
  if (state.snapshot) { state.period = button.dataset.period; renderLedger(); }
}));
document.querySelectorAll("#category-tabs button").forEach((button) => button.addEventListener("click", () => {
  if (state.snapshot) {
    state.category = button.dataset.cat;
    document.querySelectorAll("#category-tabs button").forEach((b) => b.classList.toggle("active", b === button));
    renderWatchlist();
  }
}));
document.querySelectorAll(".nav-links a").forEach((link) => link.addEventListener("click", () => {
  document.querySelectorAll(".nav-links a").forEach((node) => node.classList.toggle("active", node === link));
}));
document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => sendChat(button.dataset.prompt)));
$("chat-form").addEventListener("submit", (event) => { event.preventDefault(); sendChat($("chat-input").value); });
$("chat-input").addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); sendChat($("chat-input").value); }
});
$("token-button").addEventListener("click", () => {
  const token = window.prompt("Optional private cockpit API token. Stored only in this browser session. Leave blank for a local server without a token.", "");
  if (token === null) return;
  state.token = token.trim();
  try { if (state.token) sessionStorage.setItem("humming-bird-token", state.token); else sessionStorage.removeItem("humming-bird-token"); } catch { /* In-memory access remains available. */ }
  refresh();
});

if ($("skills-toggle")) {
  $("skills-toggle").addEventListener("click", () => {
    const drawer = $("skills-drawer");
    if (drawer) drawer.hidden = !drawer.hidden;
  });
}
if ($("close-skills")) {
  $("close-skills").addEventListener("click", () => {
    const drawer = $("skills-drawer");
    if (drawer) drawer.hidden = true;
  });
}
if ($("rollback-button")) {
  $("rollback-button").addEventListener("click", () => mutate(async () => {
    try {
      const res = await api("/api/hermes/rollback", { method: "POST" });
      await refresh(true);
      notify(`Rollback executed: reverted ${res.action_reverted} (${res.description})`);
    } catch (err) {
      showError(err.message);
    }
  }));
}

if ($("treemap-back-btn")) {
  $("treemap-back-btn").addEventListener("click", () => {
    state.activeSector = null;
    renderMarketMap();
  });
}

window.addEventListener("resize", () => {
  if (state.snapshot && state.snapshot.market_map) {
    renderMarketMap();
    renderTopSectorsChart();
  }
});

function initMarketMapResizeObserver() {
  const target = $("market-map") || $("treemap-container");
  if (target && typeof ResizeObserver !== "undefined") {
    let rAF = null;
    let lastW = 0;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const cr = entry.contentRect;
        if (cr && Math.round(cr.width) !== lastW) {
          lastW = Math.round(cr.width);
          if (rAF) cancelAnimationFrame(rAF);
          rAF = requestAnimationFrame(() => {
            if (state.snapshot && state.snapshot.market_map) {
              renderMarketMap();
              renderTopSectorsChart();
            }
          });
        }
      }
    });
    ro.observe(target);
  }
}
initMarketMapResizeObserver();

// --- Theme Switcher Logic ---
function initTheme() {
  const saved = localStorage.getItem("humming-bird-theme") || "dark";
  const validTheme = saved === "light" ? "light" : "dark";
  setTheme(validTheme);
}

function setTheme(theme) {
  const cleanTheme = theme === "light" ? "light" : "dark";
  state.theme = cleanTheme;
  document.documentElement.setAttribute("data-theme", cleanTheme);
  try { localStorage.setItem("humming-bird-theme", cleanTheme); } catch { /* Optional */ }
  const nameElem = $("theme-name");
  if (nameElem) {
    nameElem.textContent = cleanTheme === "dark" ? "Dark" : "Light";
  }
}

function toggleTheme() {
  const next = state.theme === "dark" ? "light" : "dark";
  setTheme(next);
}

// --- DSE Live Market Clock & Countdown ---
function tickMarketClock() {
  const dot = $("market-status-dot");
  const statusTxt = $("market-status-text");
  const countdownTxt = $("market-countdown-text");
  if (!dot || !statusTxt || !countdownTxt) return;

  const now = new Date();
  const dhakaStr = now.toLocaleString("en-US", { timeZone: "Asia/Dhaka" });
  const dhakaDate = new Date(dhakaStr);

  const dayOfWeek = dhakaDate.getDay();
  const hours = dhakaDate.getHours();
  const minutes = dhakaDate.getMinutes();
  const seconds = dhakaDate.getSeconds();
  const totalMinutes = hours * 60 + minutes;

  const openMinutes = 10 * 60;
  const closeMinutes = 14 * 60 + 30;

  const isTradingDay = dayOfWeek >= 0 && dayOfWeek <= 4;

  if (isTradingDay && totalMinutes >= openMinutes && totalMinutes < closeMinutes) {
    dot.className = "status-dot clock-dot open";
    setText("market-status-text", "DSE OPEN");
    const diffSec = (closeMinutes * 60) - (totalMinutes * 60 + seconds);
    const remH = Math.floor(diffSec / 3600);
    const remM = Math.floor((diffSec % 3600) / 60);
    const remS = diffSec % 60;
    setText("market-countdown-text", `Closes in ${String(remH).padStart(2, "0")}h ${String(remM).padStart(2, "0")}m ${String(remS).padStart(2, "0")}s`);
    if ($("topbar-clock-widget")) $("topbar-clock-widget").title = "DSE trading session open until 14:30 (Asia/Dhaka)";
    if ($("run-cycle")) $("run-cycle").title = "Run live automation cycle";
  } else {
    dot.className = "status-dot clock-dot closed";
    setText("market-status-text", "DSE CLOSED");

    let daysToAdd = 0;
    if (isTradingDay && totalMinutes < openMinutes) {
      daysToAdd = 0;
    } else {
      if (dayOfWeek === 4) daysToAdd = 3;
      else if (dayOfWeek === 5) daysToAdd = 2;
      else if (dayOfWeek === 6) daysToAdd = 1;
      else daysToAdd = 1;
    }

    const nextSession = new Date(dhakaDate);
    nextSession.setDate(nextSession.getDate() + daysToAdd);
    nextSession.setHours(10, 0, 0, 0);
    const dayNames = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    const nextDayName = dayNames[nextSession.getDay()];
    if ($("topbar-clock-widget")) $("topbar-clock-widget").title = `DSE opens ${nextDayName} 10:00 (Asia/Dhaka)`;
    if ($("run-cycle")) $("run-cycle").title = "Market closed: runs on demo data";

    const diffMs = nextSession.getTime() - dhakaDate.getTime();
    if (diffMs > 0) {
      const diffSec = Math.floor(diffMs / 1000);
      const remH = Math.floor(diffSec / 3600);
      const remM = Math.floor((diffSec % 3600) / 60);
      const remS = diffSec % 60;
      setText("market-countdown-text", `Next: ${remH}h ${remM}m ${remS}s`);
    } else {
      setText("market-countdown-text", "Opens at 10:00 AM");
    }
  }
}

// --- Wire Event Handlers ---
if ($("theme-toggle-btn")) {
  $("theme-toggle-btn").addEventListener("click", toggleTheme);
}

function tickClock() {
  setText("dhaka-clock", clockFormat.format(new Date()));
  tickMarketClock();
}
tickClock();
setInterval(tickClock, 1000);
initTheme();
setInterval(() => { if (!document.hidden && !state.busy && !state.allocationDirty) refresh(true); }, 20000);
document.addEventListener("visibilitychange", () => { if (!document.hidden && !state.busy) refresh(true); });
function renderAutomationControlBar() {
  if (!state.snapshot) return;
  const app = state.snapshot.app || {};
  const adapter = state.snapshot.adapter || {};
  const enabled = app.automation_enabled !== undefined ? Boolean(app.automation_enabled) : !app.paused;
  const mode = app.ingestion_mode || "BACKGROUND_POLLING";
  const interval = Number(app.polling_interval_sec || 120);

  // Master switch (Settings)
  const masterBtn = $("master-automation-toggle");
  if (masterBtn) {
    masterBtn.classList.toggle("is-active", enabled);
    masterBtn.classList.toggle("is-paused", !enabled);
    masterBtn.disabled = state.busy;
  }
  const statusText = $("master-automation-status-text");
  if (statusText) {
    statusText.textContent = enabled ? "ON" : "OFF";
    statusText.className = `toggle-status-plain ${enabled ? "is-on" : "is-off"}`;
  }
  const toggleInput = $("master-automation-toggle-input");
  if (toggleInput) {
    toggleInput.checked = enabled;
    toggleInput.disabled = state.busy;
  }

  // Topbar Engine Switch
  const topbarInput = $("topbar-automation-toggle-input");
  if (topbarInput) {
    topbarInput.checked = enabled;
    topbarInput.disabled = state.busy;
  }
  const topbarStatusText = $("topbar-engine-status-text");
  if (topbarStatusText) {
    topbarStatusText.textContent = enabled ? "Engine ON" : "Engine OFF";
    topbarStatusText.className = `engine-switch-label ${enabled ? "is-active" : "is-paused"}`;
  }

  // Segmented mode buttons (Settings Page)
  const isLive = mode === "ONSCREEN_LIVE" || mode === "SIDE_BY_SIDE_LIVE";
  const pollingBtn = $("mode-btn-polling");
  const liveBtn = $("mode-btn-live");
  if (pollingBtn) {
    pollingBtn.classList.toggle("active", mode === "BACKGROUND_POLLING");
    pollingBtn.disabled = state.busy;
  }
  if (liveBtn) {
    liveBtn.classList.toggle("active", isLive);
    liveBtn.disabled = state.busy;
  }
  const modePill = $("current-mode-pill");
  if (modePill) {
    modePill.textContent = mode === "BACKGROUND_POLLING" ? "Method A Active" : "Method B Active";
  }

  // Header Mode Slider (Portfolio Overview Header)
  const hdrPolling = $("hdr-mode-polling");
  const hdrLive = $("hdr-mode-live");
  if (hdrPolling) {
    hdrPolling.classList.toggle("active", mode === "BACKGROUND_POLLING");
    hdrPolling.disabled = state.busy;
  }
  if (hdrLive) {
    hdrLive.classList.toggle("active", isLive);
    hdrLive.disabled = state.busy;
  }
  const overflowPolling = $("overflow-mode-polling");
  const overflowLive = $("overflow-mode-live");
  if (overflowPolling) {
    overflowPolling.classList.toggle("active", mode === "BACKGROUND_POLLING");
    overflowPolling.disabled = state.busy;
  }
  if (overflowLive) {
    overflowLive.classList.toggle("active", isLive);
    overflowLive.disabled = state.busy;
  }

  // Polling Range Slider & Interval Pills
  const intervalWrap = $("polling-interval-wrap");
  const isPollingActive = enabled && mode === "BACKGROUND_POLLING";
  if (intervalWrap) {
    intervalWrap.classList.toggle("disabled", !isPollingActive);
  }
  const rangeSlider = $("polling-range-slider");
  if (rangeSlider) {
    rangeSlider.value = interval;
    rangeSlider.disabled = state.busy || !isPollingActive;
  }
  const intervalDisplay = $("polling-interval-display");
  if (intervalDisplay) {
    intervalDisplay.textContent = `${interval}s`;
  }
  document.querySelectorAll("#polling-interval-pills .pill-btn").forEach((pill) => {
    const pillSec = Number(pill.dataset.sec);
    pill.classList.toggle("active", pillSec === interval);
    pill.disabled = state.busy || !isPollingActive;
  });

  // Adapter status badge
  const dot = $("adapter-dot");
  const adpText = $("adapter-status-text");
  if (adpText && dot) {
    if (!enabled) {
      adpText.textContent = "Engine Paused";
      dot.className = "status-dot amber";
    } else if (mode === "BACKGROUND_POLLING") {
      adpText.textContent = `Polling Active · ${interval}s`;
      dot.className = "status-dot live-dot active";
    } else {
      adpText.textContent = "CDP Attached · Live";
      dot.className = "status-dot live-dot active";
    }
  }

  // Overview quick status pill
  const ovDot = $("overview-sys-dot");
  const ovText = $("overview-sys-text");
  if (ovText && ovDot) {
    ovText.textContent = `${mode === "BACKGROUND_POLLING" ? "Method A (" + interval + "s)" : "Method B (Onscreen Live)"} · ${enabled ? "AUTO ON" : "PAUSED"}`;
    ovDot.className = `status-dot ${enabled ? "live-dot active" : "amber"}`;
  }

  // Circuit breaker state
  const circ = $("circuit-state");
  if (circ) {
    circ.textContent = enabled ? "✓ Normal execution state" : "⚠ Master buy/sell paused";
    circ.className = `circuit-state ${enabled ? "" : "paused"}`;
  }

  // Adapter telemetry details
  const adpMode = $("adp-mode-text");
  if (adpMode) {
    adpMode.textContent = mode === "BACKGROUND_POLLING" ? `Method A (Polling · ${interval}s)` : "Method B (Onscreen Live Mode CDP)";
  }
}

async function setAutomationConfig(newConfig) {
  if (state.busy) return;
  await mutate(async () => {
    const res = await api("/api/automation/config", {
      method: "POST",
      body: newConfig,
    });
    if (state.snapshot) {
      state.snapshot.app.automation_enabled = res.automation_enabled;
      state.snapshot.app.paused = res.paused;
      state.snapshot.app.ingestion_mode = res.ingestion_mode;
      state.snapshot.app.polling_interval_sec = res.polling_interval_sec;
      state.snapshot.adapter = res.adapter;
      renderSnapshot();
    }
    const modeLabel = res.ingestion_mode === "BACKGROUND_POLLING" ? "Background Polling" : "Onscreen Live Mode";
    notify(`Automation: ${res.automation_enabled ? "ON" : "OFF"} · ${modeLabel} (${res.polling_interval_sec}s)`);
    if (res.ingestion_mode === "ONSCREEN_LIVE") {
      await refresh(true);
    }
  });
}

// Master automation bar & header mode slider event bindings
if ($("master-automation-toggle")) {
  $("master-automation-toggle").addEventListener("click", () => {
    if (!state.snapshot) return;
    const app = state.snapshot.app || {};
    const enabled = app.automation_enabled !== undefined ? Boolean(app.automation_enabled) : !app.paused;
    const mode = app.ingestion_mode || "BACKGROUND_POLLING";
    const interval = Number(app.polling_interval_sec || 120);
    setAutomationConfig({
      automation_enabled: !enabled,
      ingestion_mode: mode,
      polling_interval_sec: interval,
    });
  });
}

if ($("master-automation-toggle-input")) {
  $("master-automation-toggle-input").addEventListener("change", (e) => {
    if (!state.snapshot) return;
    const app = state.snapshot.app || {};
    const mode = app.ingestion_mode || "BACKGROUND_POLLING";
    const interval = Number(app.polling_interval_sec || 120);
    setAutomationConfig({
      automation_enabled: e.target.checked,
      ingestion_mode: mode,
      polling_interval_sec: interval,
    });
  });
}

if ($("topbar-automation-toggle-input")) {
  $("topbar-automation-toggle-input").addEventListener("change", (e) => {
    if (!state.snapshot) return;
    const app = state.snapshot.app || {};
    const mode = app.ingestion_mode || "BACKGROUND_POLLING";
    const interval = Number(app.polling_interval_sec || 120);
    setAutomationConfig({
      automation_enabled: e.target.checked,
      ingestion_mode: mode,
      polling_interval_sec: interval,
    });
  });
}

if ($("hdr-mode-polling")) {
  $("hdr-mode-polling").addEventListener("click", () => {
    setAutomationConfig({ ingestion_mode: "BACKGROUND_POLLING" });
  });
}

if ($("hdr-mode-live")) {
  $("hdr-mode-live").addEventListener("click", () => {
    setAutomationConfig({ ingestion_mode: "ONSCREEN_LIVE" });
  });
}
const overflowBtn = $("topbar-overflow-btn");
const overflowMenu = $("topbar-overflow-menu");
if (overflowBtn && overflowMenu) {
  overflowBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    const isHidden = overflowMenu.hidden;
    overflowMenu.hidden = !isHidden;
    overflowBtn.setAttribute("aria-expanded", String(isHidden));
  });
  document.addEventListener("click", (e) => {
    if (!overflowMenu.hidden && !overflowMenu.contains(e.target) && e.target !== overflowBtn) {
      overflowMenu.hidden = true;
      overflowBtn.setAttribute("aria-expanded", "false");
    }
  });
}
if ($("overflow-mode-polling")) {
  $("overflow-mode-polling").addEventListener("click", () => {
    setAutomationConfig({ ingestion_mode: "BACKGROUND_POLLING" });
    if (overflowMenu) overflowMenu.hidden = true;
  });
}
if ($("overflow-mode-live")) {
  $("overflow-mode-live").addEventListener("click", () => {
    setAutomationConfig({ ingestion_mode: "ONSCREEN_LIVE" });
    if (overflowMenu) overflowMenu.hidden = true;
  });
}

if ($("mode-btn-polling")) {
  $("mode-btn-polling").addEventListener("click", () => {
    setAutomationConfig({ ingestion_mode: "BACKGROUND_POLLING" });
  });
}

if ($("mode-btn-live")) {
  $("mode-btn-live").addEventListener("click", () => {
    setAutomationConfig({ ingestion_mode: "ONSCREEN_LIVE" });
  });
}

const pollingSlider = $("polling-range-slider");
if (pollingSlider) {
  pollingSlider.addEventListener("input", (e) => {
    const sec = Number(e.target.value);
    const disp = $("polling-interval-display");
    if (disp) disp.textContent = `${sec}s`;
    document.querySelectorAll("#polling-interval-pills .pill-btn").forEach((pill) => {
      pill.classList.toggle("active", Number(pill.dataset.sec) === sec);
    });
  });
  pollingSlider.addEventListener("change", (e) => {
    setAutomationConfig({ polling_interval_sec: Number(e.target.value) });
  });
}

document.querySelectorAll("#polling-interval-pills .pill-btn").forEach((pill) => {
  pill.addEventListener("click", () => {
    const sec = Number(pill.dataset.sec);
    const slider = $("polling-range-slider");
    if (slider) slider.value = sec;
    const disp = $("polling-interval-display");
    if (disp) disp.textContent = `${sec}s`;
    setAutomationConfig({ polling_interval_sec: sec });
  });
});

function initRealtimeStream() {
  if (typeof EventSource === "undefined") return;
  try {
    const source = new EventSource("/api/stream");
    source.onopen = () => {
      const dot = $("live-dot");
      if (dot) dot.classList.add("active");
    };
    source.addEventListener("cycle", () => { if (!state.busy && !state.allocationDirty) refresh(true); });
    source.addEventListener("advance", () => { if (!state.busy && !state.allocationDirty) refresh(true); });
    source.addEventListener("allocation", () => { if (!state.busy && !state.allocationDirty) refresh(true); });
    source.addEventListener("pause", () => { if (!state.busy && !state.allocationDirty) refresh(true); });
    source.addEventListener("automation_config", () => { if (!state.busy && !state.allocationDirty) refresh(true); });
    source.addEventListener("agentic_action", () => { if (!state.busy && !state.allocationDirty) refresh(true); });
    source.addEventListener("rollback", () => { if (!state.busy && !state.allocationDirty) refresh(true); });
    source.addEventListener("market_map", () => { if (!state.busy && !state.allocationDirty) refresh(true); });
    source.onerror = () => {
      const dot = $("live-dot");
      if (dot) dot.classList.remove("active");
    };
  } catch (err) {
    /* Fallback to interval refresh */
  }
}

// --- Multi-View Navigation Router ---
function switchView(viewName) {
  viewName = (viewName || "overview").replace("#", "");
  const isSettings = viewName === "settings" || viewName === "system-control";
  const viewDashboard = $("view-dashboard");
  const viewSettings = $("view-settings");

  // Update nav-rail items
  document.querySelectorAll(".nav-rail .nav-item").forEach((el) => {
    const href = el.getAttribute("href") || "";
    const target = href.replace("#", "");
    if (isSettings) {
      el.classList.toggle("active", target === "settings" || target === "system-control");
    } else {
      el.classList.toggle("active", target === viewName || (!viewName && target === "overview"));
    }
  });

  if (isSettings) {
    if (viewDashboard) {
      viewDashboard.classList.remove("active");
      viewDashboard.hidden = true;
    }
    if (viewSettings) {
      viewSettings.classList.add("active");
      viewSettings.hidden = false;
    }
    const workspace = document.querySelector(".workspace");
    if (workspace) workspace.scrollTo({ top: 0, behavior: "smooth" });
    loadApiKeysSettings();
  } else {
    if (viewSettings) {
      viewSettings.classList.remove("active");
      viewSettings.hidden = true;
    }
    if (viewDashboard) {
      viewDashboard.classList.add("active");
      viewDashboard.hidden = false;
    }
    const targetId = viewName || "overview";
    const targetEl = document.getElementById(targetId);
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
    }
    // Render treemap and gainers if scrolling to or past watchlist
    setTimeout(() => {
      renderMarketMap();
      renderTopSectorsChart();
    }, 50);
  }
}

function initViewRouter() {
  window.addEventListener("hashchange", () => {
    const hash = window.location.hash.slice(1);
    if (hash) switchView(hash);
  });

  document.querySelectorAll(".nav-rail .nav-item").forEach((el) => {
    el.addEventListener("click", (e) => {
      const href = el.getAttribute("href");
      if (href && href.startsWith("#")) {
        e.preventDefault();
        const target = href.slice(1);
        window.location.hash = target;
        if (typeof window.setNavClickScrolling === "function") {
          window.setNavClickScrolling();
        }
        switchView(target);
      }
    });
  });

  // Quick link in Overview session bar
  const sysLink = $("overview-sys-link");
  if (sysLink) {
    sysLink.addEventListener("click", (e) => {
      e.preventDefault();
      window.location.hash = "settings";
      switchView("settings");
    });
  }

  // Model Picker Drop-up toggle (Bottom model button above chat input)
  const modelBtn = $("hermes-model-trigger") || $("hermes-bottom-model-btn") || $("hermes-model-btn");
  const modelDrop = $("model-dropup-menu") || $("model-picker-dropdown");
  if (modelBtn && modelDrop) {
    modelBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      modelDrop.hidden = !modelDrop.hidden;
    });
    document.addEventListener("click", (e) => {
      if (!modelDrop.contains(e.target) && !modelBtn.contains(e.target)) {
        modelDrop.hidden = true;
      }
    });
  }

  // Model select in Settings page
  const settingsModelSelect = $("settings-model-select");
  if (settingsModelSelect) {
    settingsModelSelect.addEventListener("change", (e) => {
      switchHermesModel(e.target.value);
    });
  }

  // Rollback buttons
  const rbPaneBtn = $("rollback-pane-btn");
  if (rbPaneBtn) rbPaneBtn.addEventListener("click", executeRollback);
  const rbSkillsBtn = $("rollback-skills-btn");
  if (rbSkillsBtn) rbSkillsBtn.addEventListener("click", executeRollback);

  // Initial view from URL hash or default to overview
  const initialHash = window.location.hash.slice(1) || "overview";
  switchView(initialHash);
}

// --- ScrollSpy for Continuous Dashboard Sections ---
function initScrollSpy() {
  const workspace = document.querySelector(".workspace");
  if (!workspace) return;
  const sectionIds = ["overview", "watchlist", "rules", "ledger"];
  let isNavClicking = false;
  let clickTimeout = null;

  window.setNavClickScrolling = () => {
    isNavClicking = true;
    if (clickTimeout) clearTimeout(clickTimeout);
    clickTimeout = setTimeout(() => { isNavClicking = false; }, 850);
  };

  function updateActiveNav(activeId) {
    document.querySelectorAll(".nav-rail .nav-item").forEach((item) => {
      const href = item.getAttribute("href") || "";
      const target = href.replace("#", "");
      if (sectionIds.includes(target)) {
        item.classList.toggle("active", target === activeId);
      }
    });
  }

  workspace.addEventListener("scroll", () => {
    const dashboardView = $("view-dashboard");
    if (!dashboardView || dashboardView.hidden || isNavClicking) return;

    if (workspace.scrollTop + workspace.clientHeight >= workspace.scrollHeight - 45) {
      updateActiveNav("ledger");
      return;
    }

    const workspaceRect = workspace.getBoundingClientRect();
    let currentSection = sectionIds[0];

    for (const id of sectionIds) {
      const el = document.getElementById(id);
      if (el) {
        const rect = el.getBoundingClientRect();
        if (rect.top - workspaceRect.top <= 180) {
          currentSection = id;
        }
      }
    }

    updateActiveNav(currentSection);
  }, { passive: true });
}

initCharts();
updateControls();
refresh();
initRealtimeStream();
initHermesSidebar();
loadConversations();
loadHermesModels();
loadSystemChanges();
initAuthAndSettings();
initViewRouter();
initScrollSpy();
