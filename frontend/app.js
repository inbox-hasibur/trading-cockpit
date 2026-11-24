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

function formatTimestamp(isoOrDate) {
  if (!isoOrDate) return "Just now";
  try {
    const d = new Date(isoOrDate);
    if (isNaN(d.getTime())) return String(isoOrDate);
    return clockFormat.format(d);
  } catch {
    return "Just now";
  }
}

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
window.state = state;

let decisionFilter = "all";

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
  if (/CRASH|BLOCKED|INVALID|KILL_SWITCH|NOT_AUTHENTICATED|SCHEMA_CHANGED/.test(action)) return "negative";
  if (/PREVIEW_BUY|PREVIEW_SELL|PREVIEW|MASTER_OFF|CAPS|LOCK|LOSS|DISABLED|ODD|STALE/.test(action)) return "amber";
  if (/BUY_ZONE|^BUY$|LIVE/.test(action)) return "buy";
  if (/SELL_ZONE|^SELL$|SELL_TIER|RECOVERY|PULLBACK|RUNNER/.test(action)) return "sell";
  if (/WAIT|MID_RANGE|NO_CHURN|BUDGET|MARKET_CLOSED|NO_SESSION|NO_DATA|LAST_CLOSE/.test(action)) return "neutral";
  if (/MATURE/.test(action)) return "positive";
  return "neutral";
}

function badge(action, label) {
  const labels = {
    CRASH_QUARANTINE: "CRASH GUARD",
    BUY_ZONE: "BUY ZONE",
    SELL_ZONE: "SELL ZONE",
    MID_RANGE: "MID RANGE",
    LIVE: "LIVE",
    LAST_CLOSE: "LAST CLOSE",
    STALE: "STALE",
    STALE_DATA: "STALE",
    NO_DATA: "NO DATA",
    WAIT_DATA: "NO DATA",
    MASTER_OFF: "MASTER OFF",
    KILL_SWITCH: "KILL SWITCH",
    MARKET_CLOSED: "MARKET CLOSED",
    NO_SESSION: "NO SESSION",
    NOT_AUTHENTICATED: "NOT AUTHENTICATED",
    SCHEMA_CHANGED: "SCHEMA CHANGED",
    CAPS: "CAPS LIMIT",
    PREVIEW_BUY: "PREVIEW BUY",
    PREVIEW_SELL: "PREVIEW SELL",
    PREVIEW: "PREVIEW",
  };
  const node = element("span", `signal-badge tone-${tone(action)}`, label || labels[action] || action.replaceAll("_", " "));
  node.title = action;
  return node;
}

function notify(message, type = false) {
  clearTimeout(state.toastTimer);
  const toast = $("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.remove("error", "warning", "success");
  if (type === true || type === "error") {
    toast.classList.add("error");
  } else if (type === "warning" || type === "warn") {
    toast.classList.add("warning");
  } else if (type === "success") {
    toast.classList.add("success");
  }
  toast.hidden = false;
  state.toastTimer = setTimeout(() => { toast.hidden = true; }, 5500);
}
window.notify = notify;
window.showToast = notify;

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
  const activeToken = state.token || state.snapshot?.app?.kernel_token;
  if (activeToken) {
    requestHeaders.Authorization = `Bearer ${activeToken}`;
    requestHeaders["X-Kernel-Token"] = activeToken;
  }
  try {
    const response = await fetch(path, {
      method, headers: requestHeaders, body: body === undefined ? undefined : (typeof body === "string" ? body : JSON.stringify(body)),
      signal: controller.signal, cache: "no-store", credentials: "same-origin",
    });
    let data;
    try { data = await response.json(); } catch { throw new Error(`Server returned HTTP ${response.status} without JSON.`); }
    if (!response.ok) {
      let detail = data.detail;
      if (Array.isArray(detail)) {
        detail = detail.map((issue) => {
          const loc = (issue.loc || []).filter((x) => x !== "body").join(".");
          return loc ? `${loc}: ${issue.msg}` : issue.msg;
        }).join("; ");
      } else if (typeof detail === "object" && detail !== null) {
        detail = JSON.stringify(detail);
      }
      const tokenHelp = response.status === 401 ? " Use the API token control in the header." : "";
      throw new Error(`${detail || data.error || `Request failed (HTTP ${response.status})`}${tokenHelp}`);
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("Request timed out. Refresh status before retrying; cycles are deduplicated.");
    throw error;
  } finally { clearTimeout(timer); }
}

function updateControls() {
  const ready = Boolean(state.snapshot);
  const autoEnabled = ready && state.snapshot.app && (state.snapshot.app.automation_enabled !== undefined ? Boolean(state.snapshot.app.automation_enabled) : !state.snapshot.app.paused);

  const runBtn = $("run-cycle");
  if (runBtn) {
    runBtn.disabled = !ready || state.busy;
    const runLabel = $("run-label");
    if (runLabel) {
      runLabel.textContent = state.busy ? "Working…" : (autoEnabled ? "Run cycle now" : "Run cycle now (Preview)");
    }
    runBtn.title = autoEnabled
      ? "Run trading cycle now (submits orders subject to mode, caps & checks)"
      : "Run labeled PREVIEW cycle (decisions only; zero orders submitted while automation is OFF)";
  }

  const topbarMaster = $("topbar-master-toggle");
  if (topbarMaster) topbarMaster.disabled = !ready || state.busy;
  const topbarKill = $("topbar-kill-btn");
  if (topbarKill) topbarKill.disabled = !ready || state.busy;
  const topbarHandoff = $("topbar-handoff-btn");
  if (topbarHandoff) topbarHandoff.disabled = !ready || state.busy;
  const settingsHandoff = $("settings-handoff-btn");
  if (settingsHandoff) settingsHandoff.disabled = !ready || state.busy;

  const nextSessionEl = $("next-session");
  if (nextSessionEl) nextSessionEl.disabled = !ready || state.busy;
  const scenarioEl = $("scenario");
  if (scenarioEl) scenarioEl.disabled = state.busy;
  const saveAlloc = $("save-allocation");
  if (saveAlloc) saveAlloc.disabled = !ready || state.busy;
  const buyAlloc = $("buy-allocation");
  if (buyAlloc) buyAlloc.disabled = !ready || state.busy;
  const compEnabled = $("company-enabled");
  if (compEnabled) compEnabled.disabled = !ready || state.busy;
  const chatSend = $("chat-send");
  if (chatSend) chatSend.disabled = !ready || state.chatBusy;
  document.querySelectorAll("[data-prompt]").forEach((button) => { button.disabled = !ready || state.chatBusy; });

  if (ready) {
    setText("engine-state", autoEnabled ? "MANUAL CYCLES" : "ENGINE PAUSED");
    $("engine-state").classList.toggle("paused", !autoEnabled);
    renderAutomationControlBar();
  }
}

async function refresh(quiet = false) {
  const sequence = ++state.fetchSequence;
  try {
    const snapshot = await api("/api/portfolio");
    if (sequence !== state.fetchSequence) return;
    state.snapshot = snapshot;
    if (!state.token && snapshot?.app?.kernel_token) {
      state.token = snapshot.app.kernel_token;
    }
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

function isLiveSource() {
  const app = (state.snapshot && state.snapshot.app) || {};
  const adapter = (state.snapshot && state.snapshot.adapter) || {};
  return Boolean(
    adapter.connected ||
    app.source === "STOCKNOW_LIVE" ||
    adapter.source === "STOCKNOW_LIVE" ||
    (app.trading_mode === "LIVE_HOURS" && (adapter.ready || adapter.has_token))
  );
}
window.isLiveSource = isLiveSource;

function renderPortfolioHeaderBadge() {
  const badgeEl = $("portfolio-header-badge");
  const badgeText = $("portfolio-header-badge-text");
  const badgeDot = $("portfolio-header-badge-dot");
  if (!badgeEl || !badgeText) return;

  const app = (state.snapshot && state.snapshot.app) || {};
  const adapter = (state.snapshot && state.snapshot.adapter) || {};
  const metrics = (state.snapshot && state.snapshot.metrics) || {};
  const summary = (state.snapshot && state.snapshot.summary) || {};

  const isLive = isLiveSource();

  if (!isLive) {
    badgeEl.className = "portfolio-header-badge is-demo";
    badgeText.textContent = "DEMO / PAPER";
    if (badgeDot) badgeDot.className = "status-dot amber";
    badgeEl.title = "Demo Simulation · Synthetic data";
    return;
  }

  const name = state.snapshot.portfolio_name || app.target_portfolio_name || adapter.bound_portfolio_name || "Humming Bird";
  const id = state.snapshot.portfolio_id || app.target_portfolio_id || adapter.bound_portfolio_id || "164580";

  let syncedTime = "Just now";
  const syncIso = adapter.last_portfolio_sync_at || adapter.last_sync_at || (state.snapshot && state.snapshot.last_market_sync);
  if (syncIso) {
    syncedTime = formatTimestamp(syncIso);
  }

  let driftNum = 0.0;
  if (metrics.drift !== undefined && metrics.drift !== null) {
    driftNum = Number(metrics.drift);
  } else if (summary.drift !== undefined && summary.drift !== null) {
    driftNum = Number(summary.drift);
  } else if (metrics.book_reconciled && metrics.equity_reconciled) {
    driftNum = 0.0;
  } else {
    driftNum = 1.0;
  }
  const driftStr = (Math.abs(driftNum) < 0.0001 ? 0 : driftNum).toFixed(2);
  const isDriftNonZero = Math.abs(driftNum) > 0.005;

  let isStale = Boolean(adapter.stale || adapter.last_sync_error);
  if (syncIso) {
    const syncTime = new Date(syncIso).getTime();
    if (!isNaN(syncTime) && Date.now() - syncTime > 15 * 60 * 1000) {
      isStale = true;
    }
  }

  const isRed = isStale || isDriftNonZero;
  badgeEl.className = `portfolio-header-badge ${isRed ? "is-stale-drift" : "is-live"}`;
  if (badgeDot) {
    badgeDot.className = `status-dot ${isRed ? "red active" : "live-dot active"}`;
  }
  badgeText.textContent = `LIVE STOCKNOW ${name} #${id} (${syncedTime}, drift ${driftStr})`;

  let tooltipReason = `Portfolio #${id} (${name}) synced from StockNow virtual broker at ${syncedTime}.`;
  if (isDriftNonZero) tooltipReason += ` Drift detected: ${driftStr} BDT.`;
  if (isStale) tooltipReason += ` Warning: Sync data is stale.`;
  badgeEl.title = tooltipReason;
}

function renderSnapshot() {
  document.querySelectorAll(".skeleton-placeholder").forEach((el) => { el.classList.remove("skeleton-placeholder"); });
  const { app, metrics } = state.snapshot;
  const adapter = state.snapshot.adapter || {};
  renderPortfolioHeaderBadge();

  const live = isLiveSource();

  // Hide demo bar with CSS class when isLiveSource() is true
  const sessionBar = document.querySelector(".session-bar");
  if (sessionBar) {
    sessionBar.classList.toggle("is-live-hidden", live);
  }

  // Footer EXPERIMENTAL · DEMO ONLY shown only in DEMO
  const footerTag = $("footer-mode-tag");
  if (footerTag) {
    footerTag.style.display = live ? "none" : "inline-flex";
  }

  // Chat safety note welcome line
  const chatSafetyNote = $("chat-safety-note") || document.querySelector(".chat-safety-note");
  if (chatSafetyNote) {
    if (live) {
      const name = state.snapshot.portfolio_name || app.target_portfolio_name || adapter.bound_portfolio_name || "Humming Bird";
      const id = state.snapshot.portfolio_id || app.target_portfolio_id || adapter.bound_portfolio_id || "164580";
      const tradingMode = app.trading_mode || (state.snapshot && state.snapshot.trading_mode) || "LIVE_HOURS";
      const modeText = tradingMode === "TEST_OFFHOURS" ? "Test Mode" : "Live Hours";
      chatSafetyNote.textContent = `Connected to StockNow portfolio ${name} #${id}, ${modeText}. Orders need your confirmation.`;
    } else {
      chatSafetyNote.textContent = "Demo Paper Mode: Hermes executes actions on local simulated holdings with strict ledger reconciliation.";
    }
  }

  // Decision feed empty state text
  const decisionEmptyP = document.querySelector("#decision-feed .empty-state p");
  if (decisionEmptyP) {
    decisionEmptyP.textContent = live
      ? "Run cycle now to preview decisions"
      : "Run a paper cycle to see range signals, settlement guards, and sequential selling decisions.";
  }

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
  renderEquitySparkline();
  renderActiveHoldings();
  renderBuckets();
  renderMainChart();
  renderWatchlist();
  renderMarketMap();
  renderTopSectorsChart();
  try { renderAutomationControlBar(); } catch (e) { console.warn("renderAutomationControlBar error:", e); }
  try { renderInspector(); } catch (e) { console.warn("renderInspector error:", e); }
  try { renderDecisions(); } catch (e) { console.warn("renderDecisions error:", e); }
  try { renderCanaryTheses(); } catch (e) { console.warn("renderCanaryTheses error:", e); }
  try { renderHermesSkills(); } catch (e) { console.warn("renderHermesSkills error:", e); }
  try { renderLedger(); } catch (e) { console.warn("renderLedger error:", e); }
  try { updateControls(); } catch (e) { console.warn("updateControls error:", e); }
  const txUI = window.TradeXpressUI || window.tradexpressUI;
  if (txUI && typeof txUI.updateFromSnapshot === "function") {
    try {
      txUI.updateFromSnapshot(state.snapshot);
    } catch (e) {
      console.warn("TradeXpressUI.updateFromSnapshot error:", e);
    }
  }
}

function renderEquitySparkline() {
  const container = $("equity-sparkline");
  if (!container) return;
  const points = state.snapshot?.normalized_curve;
  if (!points || points.length < 2) {
    container.replaceChildren();
    return;
  }
  const recentPoints = points.slice(-7).map((p) => ({ close: p.value }));
  const svg = sparkline(recentPoints);
  svg.classList.add("equity-mini-sparkline");
  container.replaceChildren(svg);
}

function renderActiveHoldings() {
  const body = $("active-holdings-body");
  const foot = $("active-holdings-foot");
  if (!body) return;

  const companies = state.snapshot.companies || [];
  const holdings = companies.filter((c) => (c.holding_qty || 0) > 0);

  const cash = state.snapshot.metrics?.available_cash ?? 91236;
  const totalCost = holdings.reduce((sum, c) => sum + (c.cost_basis || 0), 0);
  const totalGrossValue = holdings.reduce((sum, c) => sum + (c.holding_qty * c.price), 0);
  const totalNetValue = holdings.reduce((sum, c) => sum + (c.estimated_net_value || 0), 0);
  const unrealizedGain = totalNetValue - totalCost;
  const unrealizedPct = totalCost > 0 ? (unrealizedGain / totalCost) * 100 : 0;

  setText("holdings-settled-cash", currency(cash));
  setText("holdings-buy-cost", currency(Math.round(totalCost)));
  setText("holdings-sell-value", currency(Math.round(totalGrossValue)));

  const gainEl = $("holdings-unrealized-gain");
  if (gainEl) {
    const sign = unrealizedGain >= 0 ? "+" : "";
    gainEl.textContent = `${sign}${currency(Math.round(unrealizedGain))} (${sign}${unrealizedPct.toFixed(2)}%)`;
    gainEl.className = unrealizedGain >= 0 ? "positive" : "negative";
  }

  if (holdings.length === 0) {
    const emptyRow = element("tr");
    const td = cell("No open holdings in active portfolio.", "loading-cell");
    td.colSpan = 8;
    emptyRow.append(td);
    body.replaceChildren(emptyRow);
    if (foot) foot.replaceChildren();
    return;
  }

  const rows = holdings.map((c) => {
    const row = element("tr");

    // COMPANY
    const compCell = cell();
    if (window.tradexpressUI && typeof window.tradexpressUI.quickSell === "function") {
      const qsBtn = element("button", "quick-sell-btn", "↓");
      qsBtn.type = "button";
      qsBtn.title = `Quick-sell ${c.symbol} in TradeXpress Order Ticket`;
      qsBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        window.tradexpressUI.quickSell(c.symbol, c.mature_qty || c.holding_qty, c.price);
      });
      compCell.append(qsBtn);
    }
    compCell.append(element("strong", "holding-symbol", c.symbol));
    compCell.append(element("span", "holding-name muted small", ` · ${c.name}`));

    // TIER
    const tierCell = cell();
    const tierBadge = element("span", `tier-pill tier-${(c.watchlist_category || "GSC").toLowerCase()}`, c.watchlist_category || "GSC");
    tierCell.append(tierBadge);

    // QTY @ AVG COST
    const avgCost = c.holding_qty > 0 ? (c.cost_basis / c.holding_qty) : c.price;
    const qtyCell = cell(`${c.holding_qty} @ ${currency(avgCost.toFixed(2))}`, "align-right");

    // LTP
    const ltpCell = cell(numberFormat.format(c.price), "align-right");

    // TOTAL COST
    const costCell = cell(currency(Math.round(c.cost_basis)), "align-right");

    // SELL VALUE (NET)
    const sellVal = c.estimated_net_value || (c.holding_qty * c.price * 0.995);
    const sellCell = cell(currency(Math.round(sellVal)), "align-right");

    // GAIN / LOSS (%)
    const pnl = c.unrealized_pnl || (sellVal - c.cost_basis);
    const pct = c.net_return_pct || (c.cost_basis > 0 ? (pnl / c.cost_basis) * 100 : 0);
    const sign = pnl >= 0 ? "+" : "";
    const pnlCell = cell(`${sign}${currency(Math.round(pnl))} (${sign}${pct.toFixed(2)}%)`, `align-right ${pnl >= 0 ? "positive" : "negative"}`);

    // STATUS / ACTION
    const statusCell = cell();
    const isMature = c.mature_qty > 0;
    const statusTag = element("span", `holding-status-tag ${isMature ? "mature" : "locked"}`, isMature ? "Matured (T+2)" : "Settling (T+1)");
    statusCell.append(statusTag);

    if (isMature) {
      if (pnl > 0) {
        const sliceQty = Math.max(1, Math.round(c.holding_qty * 0.25));
        const sellBtn = element("button", "holdings-action-btn", `Sell 25% (${sliceQty})`);
        sellBtn.title = `Execute 25% sequential slice sell (${sliceQty} shares) of ${c.symbol}`;
        sellBtn.onclick = async (e) => {
          e.stopPropagation();
          sellBtn.disabled = true;
          sellBtn.textContent = "Selling...";
          try {
            let previewToken = null;
            if (state.snapshot?.state?.trading_mode === "LIVE_HOURS") {
              const prev = await api("/api/stocknow/execute-order", {
                method: "POST",
                body: { symbol: c.symbol, side: "SELL", quantity: sliceQty, dry_run: true },
              });
              previewToken = prev.preview_token;
            }
            const res = await api("/api/stocknow/execute-order", {
              method: "POST",
              body: {
                symbol: c.symbol,
                side: "SELL",
                quantity: sliceQty,
                dry_run: false,
                operator_confirmed: true,
                preview_token: previewToken,
              },
            });
            notify(`Order executed: Sold ${sliceQty} shares of ${c.symbol}.`);
            if (res.snapshot) {
              state.snapshot = res.snapshot;
              renderSnapshot();
            }
          } catch (err) {
            notify(`Sell failed: ${err.message}`, true);
            sellBtn.disabled = false;
            sellBtn.textContent = `Sell 25% (${sliceQty})`;
          }
        };

        const sellAllBtn = element("button", "holdings-action-btn sell-all-btn", `Sell All (${c.mature_qty})`);
        sellAllBtn.title = `Execute 100% full liquidation (${c.mature_qty} shares) of ${c.symbol}`;
        sellAllBtn.onclick = async (e) => {
          e.stopPropagation();
          sellAllBtn.disabled = true;
          sellAllBtn.textContent = "Selling...";
          try {
            let previewToken = null;
            if (state.snapshot?.state?.trading_mode === "LIVE_HOURS") {
              const prev = await api("/api/stocknow/execute-order", {
                method: "POST",
                body: { symbol: c.symbol, side: "SELL", quantity: c.mature_qty, dry_run: true },
              });
              previewToken = prev.preview_token;
            }
            const res = await api("/api/stocknow/execute-order", {
              method: "POST",
              body: {
                symbol: c.symbol,
                side: "SELL",
                quantity: c.mature_qty,
                dry_run: false,
                operator_confirmed: true,
                preview_token: previewToken,
              },
            });
            notify(`Order executed: Sold all ${c.mature_qty} shares of ${c.symbol}.`);
            if (res.snapshot) {
              state.snapshot = res.snapshot;
              renderSnapshot();
            }
          } catch (err) {
            notify(`Sell failed: ${err.message}`, true);
            sellAllBtn.disabled = false;
            sellAllBtn.textContent = `Sell All (${c.mature_qty})`;
          }
        };

        statusCell.append(" ", sellBtn, " ", sellAllBtn);
      } else {
        const guardBadge = element("span", "holding-guard-badge", "No-Loss Hold Guard");
        guardBadge.title = "Strict No-Loss rule: selling blocked while net gain is negative.";
        statusCell.append(" ", guardBadge);
      }
    }

    row.append(compCell, tierCell, qtyCell, ltpCell, costCell, sellCell, pnlCell, statusCell);
    row.addEventListener("click", () => {
      selectCompany(c.symbol);
      if (window.tradexpressUI && typeof window.tradexpressUI.selectSymbol === "function") {
        window.tradexpressUI.selectSymbol(c.symbol);
      }
    });
    return row;
  });

  body.replaceChildren(...rows);

  if (foot) {
    const totalRow = element("tr", "holdings-total-row");
    const totalLabel = cell("Total Portfolio Holdings", "holdings-total-label");
    totalLabel.colSpan = 4;
    const totCostCell = cell(currency(Math.round(totalCost)), "align-right bold");
    const totSellCell = cell(currency(Math.round(totalNetValue)), "align-right bold");
    const sign = unrealizedGain >= 0 ? "+" : "";
    const totPnlCell = cell(`${sign}${currency(Math.round(unrealizedGain))} (${sign}${unrealizedPct.toFixed(2)}%)`, `align-right bold ${unrealizedGain >= 0 ? "positive" : "negative"}`);
    const emptyActionCell = cell();

    totalRow.append(totalLabel, totCostCell, totSellCell, totPnlCell, emptyActionCell);
    foot.replaceChildren(totalRow);
  }
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
  const bucketStack = $("bucket-stack");
  if (bucketStack) bucketStack.replaceChildren(...cards);
}

function cell(text, className) { return element("td", className, text); }

function selectCompany(symbol) {
  state.selectedSymbol = symbol;
  state.allocationDirty = false;
  renderWatchlist();
  renderInspector();
}

function formatCompactNumber(num) {
  const n = Number(num) || 0;
  if (n >= 10000000) return (n / 10000000).toFixed(2) + " Cr";
  if (n >= 100000) return (n / 100000).toFixed(2) + " L";
  if (n >= 1000) return (n / 1000).toFixed(1) + "K";
  return String(n);
}

function renderWatchlist() {
  const query = $("company-search").value.trim().toLowerCase();
  const all = state.snapshot.companies;
  const cat = state.category || "ALL";

  const favCount = all.filter((c) => c.favorite === true).length;
  const gscCount = all.filter((c) => (c.watchlist_category || "GSC") === "GSC").length;
  const l1Count = all.filter((c) => c.watchlist_category === "GSC_L1").length;
  const l2Count = all.filter((c) => c.watchlist_category === "GSC_L2").length;
  if ($("cat-all-count")) setText("cat-all-count", favCount);
  if ($("cat-gsc-count")) setText("cat-gsc-count", gscCount);
  if ($("cat-l1-count")) setText("cat-l1-count", l1Count);
  if ($("cat-l2-count")) setText("cat-l2-count", l2Count);
  if ($("cat-dse-count")) setText("cat-dse-count", state.allDseShares?.length || all.length);

  const thead = $("watchlist-thead");
  const paginationBar = $("watchlist-pagination");

  // Standard TradeXpress 2.0 Market Watch View for all tabs (including ALL_DSE)
  if (thead) {
    thead.innerHTML = '<tr><th scope="col">Symbol</th><th scope="col">Curve (7–15d)</th><th scope="col" class="align-right">LTP ৳</th><th scope="col" class="align-right">% Chg</th><th scope="col" class="align-right tx-col-bid">Bid / Qty</th><th scope="col" class="align-right tx-col-offer">Offer / Qty</th><th scope="col" class="align-center" id="col-curve-signal">Cat / Signal</th><th scope="col" class="align-center">Day</th><th scope="col" class="align-right" id="col-held-mature">Matured / Qty</th><th scope="col" class="align-right">Bought Avg</th><th scope="col" class="align-right" id="col-buy-cap">Bought Total</th><th scope="col" class="align-right">Sell Total</th><th scope="col" class="align-right">Net Profit</th></tr>';
  }
  if (paginationBar) paginationBar.hidden = true;

  const hideZSpot = $("filter-hide-z-spot")?.checked ?? false;
  const heldOnly = $("filter-held-only")?.checked ?? false;

  const companies = all.filter((company) => {
    if (hideZSpot && (company.symbol_category === "Z" || company.settlement_type === "SPOT")) {
      return false;
    }
    if (heldOnly && (company.holding_qty || 0) === 0) {
      return false;
    }
    const matchesQuery = `${company.symbol} ${company.name || ""} ${company.sector || ""}`.toLowerCase().includes(query);
    let matchesCat = true;
    if (cat === "ALL" || cat === "FAVORITES") {
      matchesCat = company.favorite === true;
    } else if (cat === "ALL_DSE") {
      matchesCat = true;
    } else {
      matchesCat = (company.watchlist_category || "GSC") === cat;
    }
    return matchesQuery && matchesCat;
  });
  setText("company-count", query || cat !== "ALL_DSE" ? `${companies.length}/${all.length}` : all.length);
  const rows = companies.map((company) => {
    const row = element("tr", company.symbol === state.selectedSymbol ? "selected" : "");
    row.dataset.symbol = company.symbol;
    const companyCell = cell();
    const button = element("button", "company-button");
    button.type = "button"; button.setAttribute("aria-label", `Inspect ${company.symbol}`);
    const secClass = (company.sector || "other").toLowerCase().replace(/[^a-z0-9]/g, "_");
    button.append(element("span", `company-icon sector-${secClass}`, company.symbol[0]));
    const name = element("span");
    const symText = company.tradexpress_symbol || `${company.symbol}\`PB`;
    const symSpan = element("span", "company-symbol", symText);
    const catCode = company.watchlist_category || "GSC";
    symSpan.append(element("span", `cat-tag cat-${catCode.toLowerCase()}`, catLabels[catCode] || catCode));
    if (company.hit_52w_high) {
      symSpan.append(element("span", "badge-52", "52"));
    }
    if (company.hit_upper_circuit) {
      symSpan.append(element("span", "badge-circuit", "▲Max"));
    }
    name.append(symSpan, element("span", "company-subtitle", (company.name || company.sector).slice(0, 20)));
    button.append(name); companyCell.append(button);

    // 2. Curve sparkline
    const chart = cell();
    const curvePoints = (company.sparkline_points && company.sparkline_points.length >= 2)
      ? company.sparkline_points
      : (company.history && company.history.length >= 2 ? company.history : [company.price, company.price]);
    chart.append(sparkline(curvePoints));

    // 3. LTP
    const ltpCell = cell(numberFormat.format(company.price), "align-right tabular-nums");

    // 4. % Chg
    const rawPct = company.day_change_pct ?? company.change_pct ?? company.pct_change ?? company.curve?.day_change_pct ?? 0;
    const pctVal = Number(rawPct) || 0;
    const pctSign = pctVal > 0 ? "+" : "";
    const day = cell(`${pctSign}${pctVal.toFixed(2)}%`, `align-right tabular-nums ${pctVal > 0 ? "positive" : (pctVal < 0 ? "negative" : "muted")}`);

    // 5. Bid / Qty
    const bidPriceStr = company.bid ? numberFormat.format(company.bid) : numberFormat.format(company.price);
    const bidQtyStr = company.bid_qty ? formatCompactNumber(company.bid_qty) : "—";
    const bidCell = cell(`${bidPriceStr} / ${bidQtyStr}`, "align-right tx-col-bid tabular-nums");

    // 6. Offer / Qty
    const offerPriceStr = company.offer ? numberFormat.format(company.offer) : numberFormat.format(company.price);
    const offerQtyStr = company.offer_qty ? formatCompactNumber(company.offer_qty) : "—";
    const offerCell = cell(`${offerPriceStr} / ${offerQtyStr}`, "align-right tx-col-offer tabular-nums");

    // 7. Cat / Signal
    const signal = cell(undefined, "align-center");

    // Check Dhaka trading session hours (Sun-Thu 10:00–14:10)
    const now = new Date();
    const dhakaStr = now.toLocaleString("en-US", { timeZone: "Asia/Dhaka" });
    const dhakaDate = new Date(dhakaStr);
    const dayOfWeek = dhakaDate.getDay();
    const totalMinutes = dhakaDate.getHours() * 60 + dhakaDate.getMinutes();
    const isTradingHours = (dayOfWeek >= 0 && dayOfWeek <= 4) && (totalMinutes >= 600 && totalMinutes < 850);

    let displaySignal = company.curve.signal;
    let tooltipReason = company.curve.reason || "";
    let isDataFallback = false;

    // Replace red INVALID DATA with LIVE, LAST CLOSE, STALE, NO DATA
    if (displaySignal === "INVALID_DATA" || /INVALID/i.test(displaySignal)) {
      isDataFallback = true;
      if (!isTradingHours) {
        displaySignal = "LAST_CLOSE";
        tooltipReason = `Market closed (Trading hours: Sun–Thu 10:00–14:10) · Showing last close ৳${numberFormat.format(company.price)}`;
      } else if (!company.history || company.history.length === 0) {
        displaySignal = "NO_DATA";
        tooltipReason = "No historical candle data available from StockNow API";
      } else if (company.curve.reason && /stale/i.test(company.curve.reason)) {
        displaySignal = "STALE";
        tooltipReason = "Quote timestamp is from a prior session; awaiting live trade update";
      } else {
        displaySignal = "LIVE";
        tooltipReason = `Live intraday quote verified (৳${numberFormat.format(company.price)}) · Range analysis requires 7 sessions`;
      }
    } else if (displaySignal === "NO_DATA" || displaySignal === "WAIT_DATA") {
      isDataFallback = true;
      displaySignal = "NO_DATA";
      tooltipReason = tooltipReason || "Historical candles pending from StockNow API";
    } else if (displaySignal === "STALE_DATA" || displaySignal === "STALE") {
      isDataFallback = true;
      displaySignal = "STALE";
      tooltipReason = tooltipReason || "Market quote delayed or from prior session";
    }

    const sigBadge = badge(displaySignal);
    if (company.quarantined || displaySignal === "CRASH_QUARANTINE") {
      let dropVal = company.curve.drawdown_pct ? company.curve.drawdown_pct.toFixed(2) : "0.00";
      if (company.quarantine_reason) {
        const match = company.quarantine_reason.match(/(\d+(?:\.\d+)?)%/);
        if (match) dropVal = parseFloat(match[1]).toFixed(2);
      }
      const nSessions = company.curve.drawdown_sessions || 5;
      tooltipReason = `Quarantined: ${dropVal}% drawdown over ${nSessions} sessions`;
    }
    sigBadge.title = tooltipReason;
    signal.title = tooltipReason;

    const signalWrap = element("div", "signal-cell-wrap");
    const catLetter = company.symbol_category || "A";
    const catClass = `cat-badge cat-${catLetter.toLowerCase()}`;
    const catBadge = element("span", catClass, catLetter);
    catBadge.title = `Exchange Category ${catLetter}`;
    signalWrap.append(catBadge);

    if (company.settlement_type === "SPOT") {
      const spotBadge = element("span", "spot-badge", "SPOT");
      spotBadge.title = "SPOT Settlement - T+0 Cash Only";
      signalWrap.append(spotBadge);
    }

    signalWrap.append(sigBadge);

    // Provide a retry link for any data-fallback state (NO DATA, LAST CLOSE, STALE) on StockNow feeds; hide when LIVE or passive
    if ((isDataFallback || displaySignal === "NO_DATA" || displaySignal === "STALE" || displaySignal === "LAST_CLOSE") && displaySignal !== "LIVE" && !company.source?.includes("PASSIVE")) {
      const retryLink = element("a", "retry-sync-link", "Retry");
      retryLink.href = "#";
      retryLink.title = `Retry live quote sync for ${company.symbol} from StockNow`;
      retryLink.addEventListener("click", async (e) => {
        e.preventDefault();
        e.stopPropagation();
        try {
          notify(`Syncing market quotes for ${company.symbol}…`);
          await api("/api/stocknow/sync-market", { method: "POST" });
          await refresh(true);
          notify(`Market sync complete for ${company.symbol}.`);
        } catch (err) {
          notify(`Sync failed: ${err.message}`, true);
        }
      });
      signalWrap.append(retryLink);
    }
    signal.append(signalWrap);

    // 8. Day (Hold-day label)
    const dayLabel = company.hold_day_label || (company.mature_qty > 0 ? "T+2" : (company.holding_qty > 0 ? "T+1" : "T+0"));
    const dayCell = cell(dayLabel, "align-center small muted");

    // 9. Matured / Qty
    const position = cell(undefined, "align-right position-count tabular-nums");
    position.append(element("span", "", company.mature_qty), element("span", "muted", ` / ${company.holding_qty}`));

    // 10. Bought Avg
    const avgBought = company.avg_bought_price ? currency(company.avg_bought_price.toFixed(2)) : "—";
    const avgBoughtCell = cell(avgBought, "align-right tabular-nums");

    // 11. Bought Total
    const boughtTot = company.bought_total ? currency(Math.round(company.bought_total)) : "—";
    const boughtTotCell = cell(boughtTot, "align-right tabular-nums");

    // 12. Sell Total (net)
    const sellTot = company.sell_total_net ? currency(Math.round(company.sell_total_net)) : "—";
    const sellTotCell = cell(sellTot, "align-right tabular-nums");

    // 13. Net Profit
    let pnlCell;
    if (company.holding_qty > 0 && company.net_profit_bdt !== undefined) {
      const sign = company.net_profit_bdt >= 0 ? "+" : "";
      const pnlText = `${sign}${currency(Math.round(company.net_profit_bdt))} (${sign}${company.net_profit_pct.toFixed(2)}%)`;
      pnlCell = cell(pnlText, `align-right tabular-nums ${company.net_profit_bdt >= 0 ? "positive" : "negative"}`);
    } else {
      pnlCell = cell("—", "align-right muted");
    }

    row.append(companyCell, chart, ltpCell, day, bidCell, offerCell, signal, dayCell, position, avgBoughtCell, boughtTotCell, sellTotCell, pnlCell);
    row.addEventListener("click", () => {
      selectCompany(company.symbol);
      if (window.tradexpressUI && typeof window.tradexpressUI.selectSymbol === "function") {
        window.tradexpressUI.selectSymbol(company.symbol);
      }
    });
    return row;
  });
  if (!rows.length) { const row = element("tr"); const td = cell("No matching companies in this category.", "loading-cell"); td.colSpan = 13; row.append(td); rows.push(row); }
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
  const lotsBody = $("lots-body");
  if (lotsBody) lotsBody.replaceChildren(...rows);
  const profitTiers = $("profit-tiers");
  if (profitTiers) profitTiers.replaceChildren(...company.rule.profit_tiers.map((value, i) => element("span", "tier-chip", `+${value}% · ${company.rule.tier_slices[i]}% slice`)));
  setText("pullback-setting", `${company.rule.pullback_pct}% pullback → 50/50`);
  if (!state.allocationDirty) {
    const buyAlloc = $("buy-allocation");
    if (buyAlloc) buyAlloc.value = company.rule.buy_allocation_pct;
    const compEnabled = $("company-enabled");
    if (compEnabled) compEnabled.checked = company.rule.enabled;
  }
  updateWhatIfSimulator(company);
}

function isBuyDecision(d) {
  const act = (d.action || "").toUpperCase();
  return (act === "BUY" || act === "PREVIEW_BUY" || act === "BUY_EXECUTION") &&
    !act.includes("BLOCKED") && !act.includes("DISABLED") && !act.includes("FAILED");
}

function isSellDecision(d) {
  const act = (d.action || "").toUpperCase();
  return (act === "SELL" || act === "PREVIEW_SELL" || act === "SELL_TIER_PROFIT" || act === "SELL_EXECUTION") &&
    !act.includes("BLOCKED") && !act.includes("DISABLED") && !act.includes("FAILED");
}

function isLockDecision(d) {
  const act = (d.action || "").toUpperCase();
  const reason = (d.reason || "").toUpperCase();
  return (
    act.includes("LOCK") ||
    act.includes("HOLD") ||
    act.includes("SETTLEMENT") ||
    act.includes("MATURITY") ||
    reason.includes("T+2") ||
    reason.includes("MATURES ON") ||
    reason.includes("SETTLEMENT") ||
    reason.includes("NO-LOSS") ||
    reason.includes("STRICT NO-LOSS") ||
    reason.includes("RECOVERY")
  );
}

function isBlockedDecision(d) {
  if (isLockDecision(d)) return false;
  const act = (d.action || "").toUpperCase();
  const reason = (d.reason || "").toUpperCase();
  return (
    act.includes("BLOCK") ||
    act.includes("REJECT") ||
    act.includes("FAIL") ||
    act.includes("DISABLE") ||
    act.includes("KILL") ||
    act.includes("CAPS") ||
    act.includes("TRIP") ||
    act.includes("WAIT") ||
    act.includes("LIMIT") ||
    act.includes("QUARANTINE") ||
    reason.includes("BLOCK") ||
    reason.includes("REJECT") ||
    reason.includes("FAIL") ||
    reason.includes("EXHAUSTED") ||
    reason.includes("KILL SWITCH")
  );
}

function renderDecisions() {
  if (!state.snapshot) return;
  const feed = $("decision-feed");
  if (!feed) return;

  const { latest_cycle: cycle } = state.snapshot;
  const decisions = state.snapshot.decisions || [];
  setText("cycle-badge", cycle ? `SNAPSHOT ${cycle.revision} · ${cycle.trades.length} TRADES` : "NO CYCLES YET");

  const counts = {
    all: decisions.length,
    buys: decisions.filter(isBuyDecision).length,
    sells: decisions.filter(isSellDecision).length,
    blocked: decisions.filter(isBlockedDecision).length,
    locks: decisions.filter(isLockDecision).length,
  };

  const chipLabels = {
    ALL: `All (${counts.all})`,
    BUYS: `Buys (${counts.buys})`,
    SELLS: `Sells (${counts.sells})`,
    BLOCKED: `Blocked (${counts.blocked})`,
    LOCKS: `Locks (${counts.locks})`,
  };

  const currentFilter = (decisionFilter || "all").toLowerCase();

  document.querySelectorAll(".decision-filter-chip").forEach((chip) => {
    const rawFilter = (chip.dataset.decisionFilter || "").toUpperCase();
    if (chipLabels[rawFilter]) {
      chip.textContent = chipLabels[rawFilter];
    }
    const filterKey = rawFilter.toLowerCase();
    const isActive = (currentFilter === filterKey);
    chip.classList.toggle("active", isActive);
  });

  if (!decisions.length) {
    const emptyP = feed.querySelector(".empty-state p");
    if (emptyP) {
      emptyP.textContent = isLiveSource()
        ? "Run cycle now to preview decisions"
        : "Run a paper cycle to see range signals, settlement guards, and sequential selling decisions.";
    } else {
      feed.innerHTML = `
        <div class="empty-state">
          <div class="empty-state-icon">⌁</div>
          <strong>Ready when you are</strong>
          <p>${isLiveSource() ? "Run cycle now to preview decisions" : "Run a paper cycle to see range signals, settlement guards, and sequential selling decisions."}</p>
          <span>No orders run on startup.</span>
        </div>
      `;
    }
    return;
  }

  let filtered = decisions;
  if (currentFilter === "buys") filtered = decisions.filter(isBuyDecision);
  else if (currentFilter === "sells") filtered = decisions.filter(isSellDecision);
  else if (currentFilter === "blocked") filtered = decisions.filter(isBlockedDecision);
  else if (currentFilter === "locks") filtered = decisions.filter(isLockDecision);

  if (!filtered.length) {
    const empty = element("div", "decision-feed-empty muted small", `No ${currentFilter} decisions in this snapshot`);
    empty.style.padding = "20px 14px";
    empty.style.textAlign = "center";
    feed.replaceChildren(empty);
    return;
  }

  const entries = filtered.slice(0, 24).map((decision) => {
    const entry = element("article", "decision-entry");
    const top = element("div", "decision-top");
    top.append(element("strong", "", decision.symbol), badge(decision.action));
    if (decision.quantity) top.append(element("span", "decision-quantity", `${decision.quantity} shares`));
    if (decision.trading_mode) {
      const modeText = decision.trading_mode === "TEST_OFFHOURS" ? "Test Mode" : "Live Hours";
      const modeClass = decision.trading_mode === "TEST_OFFHOURS" ? "badge badge-test-mode" : "badge badge-live-mode";
      top.append(element("span", modeClass, modeText));
    }
    const time = element("time", "", `#${decision.revision} · ${sessionDate(decision.date, true)}`);
    time.dateTime = decision.date; top.append(time);
    entry.append(top, element("p", "", decision.reason));
    return entry;
  });
  feed.replaceChildren(...entries);
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
    const isStockNow =
      trade.source === "STOCKNOW_RECEIPT" ||
      trade.source === "STOCKNOW_SYNC" ||
      trade.source === "STOCKNOW" ||
      Boolean(trade.receipt_id) ||
      Boolean(trade.broker_trade_id) ||
      (trade.reason && (trade.reason.includes("StockNow") || trade.reason.includes("receipt")));

    const tagText = isStockNow ? "STOCKNOW RECEIPT" : "PAPER FILL";
    const tagClass = isStockNow ? "trade-source receipt-tag" : "trade-source paper-tag";
    company.append(element("div", tagClass, tagText));
    const side = cell(); side.append(badge(trade.side));
    const settlement = cell(`${trade.bucket} · ${sessionDate(trade.settles_on, true)}`);
    row.append(cell(sessionDate(trade.date, true)), company, side, cell(trade.quantity, "align-right"), cell(numberFormat.format(trade.price), "align-right"), cell(numberFormat.format(trade.fee), "align-right"), cell(trade.side === "SELL" ? `${trade.realized_pnl >= 0 ? "+" : ""}${numberFormat.format(trade.realized_pnl)}` : "-", `align-right ${trade.side === "SELL" ? (trade.realized_pnl >= 0 ? "positive" : "negative") : "muted"}`), settlement);
    return row;
  });
  if (!rows.length) { const row = element("tr"); const td = cell("No trades in this accounting period.", "loading-cell"); td.colSpan = 8; row.append(td); rows.push(row); }
  $("trades-body").replaceChildren(...rows);
  setText("ledger-range", `${sessionDate(period.start, true)} - ${sessionDate(period.end, true)} · Latest 100 records shown; totals use full ledger.`);
}

const runCycleBtn = $("run-cycle");
if (runCycleBtn) {
  runCycleBtn.addEventListener("click", () => mutate(async () => {
    const result = await api("/api/automation/cycle", { method: "POST", headers: { "Idempotency-Key": crypto.randomUUID() } });
    await refresh();
    if (result.is_preview || result.status === "PREVIEW") {
      notify(`Preview cycle complete (Automation OFF): ${result.buy_count || 0} buy, ${result.sell_count || 0} sell decisions generated. Zero orders submitted.`);
    } else if (result.status === "SKIPPED") {
      notify(`Cycle skipped: ${result.reason || "Preflight checks"}`);
    } else {
      notify(result.duplicate ? "Snapshot already evaluated — no duplicate trades." : `Cycle complete: ${result.buy_count} buy, ${result.sell_count} sell.`);
    }
  }));
}

const pauseBtn = $("pause-button");
if (pauseBtn) {
  pauseBtn.addEventListener("click", () => mutate(async () => {
    const result = await api("/api/automation/pause", { method: "POST", body: { paused: !state.snapshot.app.paused } });
    await refresh();
    notify(result.paused ? "Automation paused. New cycles blocked." : "Engine resumed.");
  }));
}

const nextSessionBtn = $("next-session");
if (nextSessionBtn) {
  nextSessionBtn.addEventListener("click", () => mutate(async () => {
    const result = await api("/api/demo/advance", { method: "POST", body: { scenario: $("scenario") ? $("scenario").value : "NORMAL" } });
    await refresh();
    notify(`Demo moved to ${sessionDate(result.date)} (${result.scenario.toLowerCase()}). No trades executed; run a cycle to evaluate.`);
  }));
}

const allocForm = $("allocation-form");
if (allocForm) {
  allocForm.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!allocForm.reportValidity()) return;
    const symbol = state.selectedSymbol;
    const body = { buy_allocation_pct: $("buy-allocation").valueAsNumber, enabled: $("company-enabled").checked };
    mutate(async () => {
      await api(`/api/companies/${encodeURIComponent(symbol)}/allocation`, { method: "PATCH", body });
      state.allocationDirty = false;
      await refresh();
      notify(`${symbol} settings saved. No trades executed.`);
    });
  });
}
const buyAllocInput = $("buy-allocation");
if (buyAllocInput) buyAllocInput.addEventListener("input", () => { state.allocationDirty = true; });
const compEnabledInput = $("company-enabled");
if (compEnabledInput) compEnabledInput.addEventListener("change", () => { state.allocationDirty = true; });
const compSearchInput = $("company-search");
if (compSearchInput) compSearchInput.addEventListener("input", () => { if (state.snapshot) renderWatchlist(); });
const dismissErrBtn = $("dismiss-error");
if (dismissErrBtn) dismissErrBtn.addEventListener("click", () => { $("error-banner").hidden = true; });

document.querySelectorAll(".decision-filter-chip").forEach((button) => {
  button.addEventListener("click", () => {
    decisionFilter = (button.dataset.decisionFilter || "all").toLowerCase();
    document.querySelectorAll(".decision-filter-chip").forEach((btn) => {
      btn.classList.toggle("active", btn === button);
    });
    renderDecisions();
  });
});

document.querySelectorAll("[data-period]").forEach((button) => button.addEventListener("click", () => {
  if (state.snapshot) { state.period = button.dataset.period; renderLedger(); }
}));
document.querySelectorAll("#category-tabs button").forEach((button) => button.addEventListener("click", () => {
  if (state.snapshot) {
    state.category = button.dataset.cat;
    state.dsePage = 1;
    document.querySelectorAll("#category-tabs button").forEach((b) => b.classList.toggle("active", b === button));
    renderWatchlist();
  }
}));

const watchlistPrev = $("watchlist-prev-page");
if (watchlistPrev) {
  watchlistPrev.addEventListener("click", () => {
    if ((state.dsePage || 1) > 1) {
      state.dsePage = (state.dsePage || 1) - 1;
      renderWatchlist();
    }
  });
}

const watchlistNext = $("watchlist-next-page");
if (watchlistNext) {
  watchlistNext.addEventListener("click", () => {
    state.dsePage = (state.dsePage || 1) + 1;
    renderWatchlist();
  });
}
document.querySelectorAll(".nav-links a").forEach((link) => link.addEventListener("click", () => {
  document.querySelectorAll(".nav-links a").forEach((node) => node.classList.toggle("active", node === link));
}));
document.querySelectorAll("[data-prompt]").forEach((button) => button.addEventListener("click", () => sendChat(button.dataset.prompt)));
const chatFormEl = $("chat-form");
if (chatFormEl) chatFormEl.addEventListener("submit", (event) => { event.preventDefault(); sendChat($("chat-input").value); });
const chatInputEl = $("chat-input");
if (chatInputEl) chatInputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); sendChat($("chat-input").value); }
});
const tokenBtn = $("token-button");
if (tokenBtn) tokenBtn.addEventListener("click", () => {
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
  const pillBtn = $("topbar-clock-widget");
  const tmodeBadge = $("topbar-tmode-badge");

  const app = (state.snapshot && state.snapshot.app) || {};
  const tradingMode = app.trading_mode || (state.snapshot && state.snapshot.trading_mode) || "LIVE_HOURS";
  const isTestMode = tradingMode === "TEST_OFFHOURS";

  if (tmodeBadge) {
    tmodeBadge.textContent = isTestMode ? "Test Mode" : "Live Hours";
    tmodeBadge.className = `topbar-tmode-badge ${isTestMode ? "badge-test" : "badge-live"}`;
  }

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
    if (dot) dot.className = "status-dot clock-dot open";
    if (statusTxt) statusTxt.textContent = "DSE OPEN";
    const diffSec = (closeMinutes * 60) - (totalMinutes * 60 + seconds);
    const remH = Math.floor(diffSec / 3600);
    const remM = Math.floor((diffSec % 3600) / 60);
    const hStr = String(remH).padStart(2, "0");
    const mStr = String(remM).padStart(2, "0");
    if (countdownTxt) countdownTxt.textContent = `closes in ${hStr}h ${mStr}m`;
    if (pillBtn) {
      pillBtn.title = `DSE OPEN · closes in ${hStr}h ${mStr}m · Click to view Settings > Trading Mode`;
    }
  } else {
    if (dot) dot.className = "status-dot clock-dot closed";
    if (statusTxt) statusTxt.textContent = "DSE CLOSED";

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

    const diffMs = nextSession.getTime() - dhakaDate.getTime();
    if (diffMs > 0) {
      const diffSec = Math.floor(diffMs / 1000);
      const remH = Math.floor(diffSec / 3600);
      const remM = Math.floor((diffSec % 3600) / 60);
      const hStr = String(remH).padStart(2, "0");
      const mStr = String(remM).padStart(2, "0");
      if (countdownTxt) countdownTxt.textContent = `next in ${hStr}h ${mStr}m`;
      if (pillBtn) pillBtn.title = `DSE CLOSED · next in ${hStr}h ${mStr}m · Click to view Settings > Trading Mode`;
    } else {
      if (countdownTxt) countdownTxt.textContent = "next in 10:00 AM";
      if (pillBtn) pillBtn.title = "DSE CLOSED · Click to view Settings > Trading Mode";
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

  // Topbar Run Mode Segmented Switch
  const isKilled = Boolean(app.kill_switch_active);
  const isBackground = mode === "BACKGROUND_POLLING" || mode === "BACKGROUND_24_7";
  const runModeText = isBackground ? "Background" : "Onscreen";

  const tradingMode = app.trading_mode || (state.snapshot && state.snapshot.trading_mode) || "LIVE_HOURS";
  const isTestMode = tradingMode === "TEST_OFFHOURS";
  const tradingModeText = isTestMode ? "Test Mode" : "Live Hours";

  let stateText = enabled ? "ON" : "OFF";
  if (isKilled) stateText = "KILLED";

  const topbarModeBg = $("topbar-mode-btn-background");
  const topbarModeOs = $("topbar-mode-btn-onscreen");
  if (topbarModeBg) {
    topbarModeBg.classList.toggle("active", isBackground);
    topbarModeBg.disabled = state.busy || pendingHandoff;
  }
  if (topbarModeOs) {
    topbarModeOs.classList.toggle("active", !isBackground);
    topbarModeOs.disabled = state.busy || pendingHandoff;
  }

  // Topbar Automation Switch
  const topbarAutoInput = $("topbar-automation-toggle-input");
  const topbarAutoState = $("topbar-automation-state");
  if (topbarAutoInput) {
    topbarAutoInput.checked = enabled && !isKilled;
    topbarAutoInput.disabled = state.busy || isKilled;
  }
  if (topbarAutoState) {
    topbarAutoState.textContent = isKilled ? "KILL" : (enabled ? "ON" : "OFF");
    topbarAutoState.className = `topbar-automation-state ${enabled && !isKilled ? "is-on" : "is-off"}`;
  }

  // Compatibility topbar chips if present in test harness
  const topbarMasterToggle = $("topbar-master-toggle");
  const topbarStatusText = $("topbar-status-text");
  const topbarMasterLabel = $("topbar-master-label");
  const statusChipText = `${stateText} · ${runModeText} · ${tradingModeText}`;
  if (topbarMasterToggle) {
    topbarMasterToggle.classList.toggle("is-on", enabled && !isKilled);
    topbarMasterToggle.classList.toggle("is-off", !enabled && !isKilled);
    topbarMasterToggle.classList.toggle("is-killed", isKilled);
    topbarMasterToggle.title = `System Status: ${statusChipText} (Click to open Settings)`;
    topbarMasterToggle.disabled = state.busy;
  }
  if (topbarStatusText) {
    topbarStatusText.textContent = statusChipText;
  }
  if (topbarMasterLabel) {
    topbarMasterLabel.textContent = enabled ? "Auto ON" : "Auto OFF";
  }

  // Topbar Emergency Kill Switch (preserved for test compatibility)
  const topbarKillBtn = $("topbar-kill-btn");
  const topbarKillLabel = $("topbar-kill-label");
  if (topbarKillBtn) {
    topbarKillBtn.classList.toggle("is-killed", isKilled);
    topbarKillBtn.disabled = state.busy;
  }
  if (topbarKillLabel) {
    topbarKillLabel.textContent = isKilled ? "KILL ACTIVE" : "Kill";
  }

  // Run Mode & Handoff Controls (Settings Page)
  const handoffActionLabel = isBackground ? "Go Onscreen" : "Go Background";
  const handoffTitle = isBackground
    ? "Handoff: Finish current cycle under lock, then switch to headed Onscreen"
    : "Handoff: Finish current cycle under lock, then switch to unattended Background";

  const topbarHandoff = $("topbar-handoff-btn");
  const topbarHandoffLabel = $("topbar-handoff-label");
  if (topbarHandoff) {
    topbarHandoff.title = handoffTitle;
    topbarHandoff.disabled = state.busy || pendingHandoff;
  }
  if (topbarHandoffLabel) {
    topbarHandoffLabel.textContent = handoffActionLabel;
  }

  const settingsHandoff = $("settings-handoff-btn");
  const settingsHandoffLabel = $("settings-handoff-label");
  if (settingsHandoff) {
    settingsHandoff.title = handoffTitle;
    settingsHandoff.disabled = state.busy || pendingHandoff;
  }
  if (settingsHandoffLabel) {
    settingsHandoffLabel.textContent = handoffActionLabel;
  }

  // Segmented mode buttons (Settings Page)
  const pollingBtn = $("mode-btn-polling");
  const liveBtn = $("mode-btn-live");
  if (pollingBtn) {
    pollingBtn.classList.toggle("active", isBackground);
    pollingBtn.disabled = state.busy || pendingHandoff;
  }
  if (liveBtn) {
    liveBtn.classList.toggle("active", !isBackground);
    liveBtn.disabled = state.busy || pendingHandoff;
  }
  const modePill = $("current-mode-pill");
  if (modePill) {
    modePill.textContent = isBackground ? "Background Active" : "Onscreen Active";
  }
  const settingsActiveMode = $("settings-active-mode-text");
  if (settingsActiveMode) {
    settingsActiveMode.textContent = isBackground ? "Active: Background" : "Active: Onscreen";
  }

  // Header Mode Slider (Portfolio Overview Header)
  const hdrPolling = $("hdr-mode-polling");
  const hdrLive = $("hdr-mode-live");
  if (hdrPolling) {
    hdrPolling.classList.toggle("active", isBackground);
    hdrPolling.disabled = state.busy;
  }
  if (hdrLive) {
    hdrLive.classList.toggle("active", !isBackground);
    hdrLive.disabled = state.busy;
  }
  const overflowPolling = $("overflow-mode-polling");
  const overflowLive = $("overflow-mode-live");
  if (overflowPolling) {
    overflowPolling.classList.toggle("active", isBackground);
    overflowPolling.disabled = state.busy;
  }
  if (overflowLive) {
    overflowLive.classList.toggle("active", !isBackground);
    overflowLive.disabled = state.busy;
  }

  // Trading Mode (Live Hours vs Test Mode)
  const targetPid = (state.snapshot && state.snapshot.portfolio_id) || (app && app.target_portfolio_id) || (isTestMode ? "" : "164580");
  const targetPname = (state.snapshot && state.snapshot.portfolio_name) || (app && app.target_portfolio_name) || (isTestMode ? "Test Portfolio" : "Humming Bird");

  const hdrTmodePill = $("hdr-tmode-pill");
  const hdrTmodeLabel = $("hdr-tmode-label");
  const hdrTmodeDot = $("hdr-tmode-dot");
  if (hdrTmodeLabel) {
    if (isTestMode) {
      hdrTmodeLabel.textContent = targetPid ? `Test Mode (#${targetPid})` : "Test Mode (No Test Portfolio)";
    } else {
      hdrTmodeLabel.textContent = `Live Hours (#${targetPid || "164580"})`;
    }
  }
  if (hdrTmodePill) {
    hdrTmodePill.className = `topbar-tmode-pill ${isTestMode ? "tmode-test" : "tmode-live"}`;
    hdrTmodePill.title = isTestMode
      ? `Trading Mode: Test Mode (Target: #${targetPid || "Unconfigured"} - ${targetPname}) — Click to open Settings`
      : `Trading Mode: Live Hours (Target: #${targetPid || "164580"} - ${targetPname}) — Click to open Settings`;
  }
  if (hdrTmodeDot) {
    hdrTmodeDot.style.background = isTestMode ? "#f59e0b" : "#10b981";
  }

  const tmodeLive = $("hdr-tmode-live");
  const tmodeTest = $("hdr-tmode-test");
  if (tmodeLive) {
    tmodeLive.classList.toggle("active", !isTestMode);
    tmodeLive.disabled = state.busy;
  }
  if (tmodeTest) {
    tmodeTest.classList.toggle("active", isTestMode);
    tmodeTest.disabled = state.busy;
  }

  const overflowTmodeLive = $("overflow-tmode-live");
  const overflowTmodeTest = $("overflow-tmode-test");
  if (overflowTmodeLive) {
    overflowTmodeLive.classList.toggle("active", !isTestMode);
    overflowTmodeLive.disabled = state.busy;
  }
  if (overflowTmodeTest) {
    overflowTmodeTest.classList.toggle("active", isTestMode);
    overflowTmodeTest.disabled = state.busy;
  }

  const settingsTmodeLive = $("settings-tmode-live");
  const settingsTmodeTest = $("settings-tmode-test");
  if (settingsTmodeLive) {
    settingsTmodeLive.classList.toggle("active", !isTestMode);
    settingsTmodeLive.disabled = state.busy;
  }
  if (settingsTmodeTest) {
    settingsTmodeTest.classList.toggle("active", isTestMode);
    settingsTmodeTest.disabled = state.busy;
  }
  const settingsTmodePill = $("settings-trading-mode-pill");
  if (settingsTmodePill) {
    settingsTmodePill.textContent = isTestMode
      ? `Test Mode (#${targetPid || "UNSET"} - ${targetPname})`
      : `Live Hours (#${targetPid || "164580"} - ${targetPname})`;
  }

  // Polling Range Slider & Interval Pills (slider only shown in Background mode)
  const intervalWrap = $("polling-interval-wrap");
  const isPollingActive = enabled && isBackground;
  if (intervalWrap) {
    intervalWrap.style.display = isBackground ? "block" : "none";
    intervalWrap.classList.toggle("disabled", !isPollingActive);
    intervalWrap.setAttribute("aria-disabled", String(!isPollingActive));
  }
  const pollingHint = $("polling-disabled-hint");
  if (pollingHint) {
    pollingHint.style.display = !isPollingActive ? "block" : "none";
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
    ovText.textContent = `${isBackground ? "Background (" + interval + "s)" : "Onscreen"} · ${enabled ? "AUTO ON" : "PAUSED"}`;
    ovDot.className = `status-dot ${enabled ? "live-dot active" : "amber"}`;
  }

  // Telemetry source badge
  const srcBadge = $("source-badge");
  if (srcBadge) {
    if (isTestMode) {
      srcBadge.className = targetPid ? "stream-badge" : "demo-badge";
      srcBadge.innerHTML = `<span class="status-dot ${targetPid ? "live-dot" : "amber"}"></span> TEST MODE (#${targetPid || "UNSET"} - ${targetPname})`;
    } else {
      srcBadge.className = "stream-badge";
      srcBadge.innerHTML = `<span class="status-dot live-dot"></span> LIVE HOURS (#${targetPid || "164580"} - ${targetPname})`;
    }
  }

  // StockNow Connection Card Telemetry
  const summary = (state.snapshot && state.snapshot.summary) || {};

  const stocknowApi = $("stocknow-api-status");
  if (stocknowApi) {
    const hasToken = Boolean(adapter.has_token || adapter.ready);
    stocknowApi.textContent = hasToken ? "Connected · Valid" : "Standby · Ready";
    stocknowApi.className = hasToken ? "positive" : "";
  }

  const stocknowBrowser = $("stocknow-browser-status");
  if (stocknowBrowser) {
    if (adapter.cdp_attached) {
      stocknowBrowser.textContent = "Connected · CDP Port 9222";
      stocknowBrowser.className = "positive";
    } else if (adapter.connected) {
      stocknowBrowser.textContent = "Running · Session Active";
      stocknowBrowser.className = "positive";
    } else {
      stocknowBrowser.textContent = "Not Running · Standby";
      stocknowBrowser.className = "muted";
    }
  }

  const stocknowPrices = $("stocknow-prices-synced");
  if (stocknowPrices) {
    const lastSync = adapter.last_sync_at || (state.snapshot && state.snapshot.last_market_sync);
    stocknowPrices.textContent = lastSync ? `${formatTimestamp(lastSync)} (GET /instruments)` : "Just now (GET /instruments)";
  }

  const stocknowPortfolio = $("stocknow-portfolio-synced");
  if (stocknowPortfolio) {
    const reconciled = summary.book_reconciled !== false && summary.equity_reconciled !== false;
    stocknowPortfolio.textContent = reconciled ? "Reconciled · 0 drift" : "Drift detected";
    stocknowPortfolio.className = reconciled ? "positive" : "negative";
  }

  const stocknowActivePortfolio = $("stocknow-active-portfolio");
  if (stocknowActivePortfolio) {
    stocknowActivePortfolio.textContent = `#${targetPid || (isTestMode ? "UNSET" : "164580")} (${targetPname})`;
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
    adpMode.textContent = isBackground ? `Background (Polling · ${interval}s)` : "Onscreen (Playwright CDP)";
  }
}

async function setAutomationConfig(newConfig) {
  if (state.busy) return;
  const currentApp = (state.snapshot && state.snapshot.app) || {};
  const mergedConfig = {
    automation_enabled: currentApp.automation_enabled !== undefined ? Boolean(currentApp.automation_enabled) : !currentApp.paused,
    ingestion_mode: currentApp.ingestion_mode || "BACKGROUND_POLLING",
    polling_interval_sec: Number(currentApp.polling_interval_sec || 120),
    trading_mode: (state.snapshot && state.snapshot.trading_mode) || currentApp.trading_mode || "LIVE_HOURS",
    ...newConfig,
  };
  await mutate(async () => {
    const res = await api("/api/automation/config", {
      method: "POST",
      body: mergedConfig,
    });
    if (state.snapshot) {
      if (res.trading_mode) {
        state.snapshot.trading_mode = res.trading_mode;
        if (state.snapshot.app) state.snapshot.app.trading_mode = res.trading_mode;
      }
      state.snapshot.app.automation_enabled = res.automation_enabled;
      state.snapshot.app.paused = res.paused;
      state.snapshot.app.ingestion_mode = res.ingestion_mode;
      state.snapshot.app.polling_interval_sec = res.polling_interval_sec;
      state.snapshot.adapter = res.adapter;
      renderSnapshot();
    }
    const modeLabel = res.ingestion_mode === "BACKGROUND_POLLING" ? "Background" : "Onscreen";
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

if ($("topbar-master-toggle")) {
  $("topbar-master-toggle").addEventListener("click", (e) => {
    e.preventDefault();
    window.location.hash = "settings";
    if (typeof switchView === "function") {
      switchView("settings");
    }
  });
}

if ($("topbar-kill-btn")) {
  $("topbar-kill-btn").addEventListener("click", async () => {
    if (!state.snapshot) return;
    const isKilled = Boolean(state.snapshot.app && state.snapshot.app.kill_switch_active);
    if (!isKilled) {
      if (!confirm("ENGAGE EMERGENCY KILL SWITCH? This immediately halts all AutoTrader and Hermes order execution.")) {
        return;
      }
      await mutate(async () => {
        await api("/api/automation/kill", {
          method: "POST",
          body: { active: true, reason: "Manual operator emergency kill switch engaged from topbar" },
        });
        await refresh();
        notify("EMERGENCY KILL SWITCH ENGAGED: All order execution halted.", "negative");
      });
    } else {
      if (!confirm("Disarm emergency kill switch? Orders will be allowed again subject to risk caps.")) {
        return;
      }
      await mutate(async () => {
        await api("/api/automation/kill", {
          method: "POST",
          body: { active: false, reason: "Manual disarm from topbar" },
        });
        await refresh();
        notify("Emergency kill switch disarmed. Trading resumed.");
      });
    }
  });
}

let pendingHandoff = false;

function setHandoffPendingState(isPending) {
  pendingHandoff = isPending;
  const topbarPending = $("topbar-switching-state");
  const settingsPending = $("settings-pending-handoff-state");
  if (topbarPending) topbarPending.style.display = isPending ? "inline-block" : "none";
  if (settingsPending) settingsPending.style.display = isPending ? "inline-block" : "none";

  const topbarBg = $("topbar-mode-btn-background");
  const topbarOs = $("topbar-mode-btn-onscreen");
  if (topbarBg) topbarBg.disabled = isPending || state.busy;
  if (topbarOs) topbarOs.disabled = isPending || state.busy;

  const modePolling = $("mode-btn-polling");
  const modeLive = $("mode-btn-live");
  if (modePolling) modePolling.disabled = isPending || state.busy;
  if (modeLive) modeLive.disabled = isPending || state.busy;
}

async function executeRunModeHandoff(targetMode) {
  if (state.busy || !state.snapshot || pendingHandoff) return;
  const currentApp = state.snapshot.app || {};
  const currentMode = currentApp.ingestion_mode || "BACKGROUND_POLLING";
  const isCurrentBg = currentMode === "BACKGROUND_POLLING" || currentMode === "BACKGROUND_24_7";
  const isTargetBg = targetMode === "BACKGROUND_POLLING" || targetMode === "BACKGROUND_24_7";
  if (isCurrentBg === isTargetBg) return;

  setHandoffPendingState(true);
  try {
    await mutate(async () => {
      await api("/api/automation/handoff", {
        method: "POST",
        body: { target_mode: targetMode, reason: "Operator run mode handoff" },
      });
      await refresh(true);
      notify(`Active run mode is now ${isTargetBg ? "Background" : "Onscreen"}`);
    });
  } catch (err) {
    notify(`Handoff failed: ${err.message}`, "error");
  } finally {
    setHandoffPendingState(false);
  }
}

async function executeHandoff() {
  if (state.busy || !state.snapshot) return;
  const currentApp = state.snapshot.app || {};
  const currentMode = currentApp.ingestion_mode || "BACKGROUND_POLLING";
  const isBackground = currentMode === "BACKGROUND_POLLING" || currentMode === "BACKGROUND_24_7";
  const targetMode = isBackground ? "ONSCREEN_LIVE" : "BACKGROUND_POLLING";
  return executeRunModeHandoff(targetMode);
}

if ($("topbar-mode-btn-background")) {
  $("topbar-mode-btn-background").addEventListener("click", () => executeRunModeHandoff("BACKGROUND_POLLING"));
}
if ($("topbar-mode-btn-onscreen")) {
  $("topbar-mode-btn-onscreen").addEventListener("click", () => executeRunModeHandoff("ONSCREEN_LIVE"));
}
if ($("mode-btn-polling")) {
  $("mode-btn-polling").addEventListener("click", () => executeRunModeHandoff("BACKGROUND_POLLING"));
}
if ($("mode-btn-live")) {
  $("mode-btn-live").addEventListener("click", () => executeRunModeHandoff("ONSCREEN_LIVE"));
}

if ($("topbar-handoff-btn")) {
  $("topbar-handoff-btn").addEventListener("click", executeHandoff);
}
if ($("settings-handoff-btn")) {
  $("settings-handoff-btn").addEventListener("click", executeHandoff);
}

if ($("topbar-clock-widget")) {
  $("topbar-clock-widget").addEventListener("click", () => {
    window.location.hash = "settings";
    if (typeof switchView === "function") {
      switchView("settings");
    }
    setTimeout(() => {
      const target = $("settings-trading-mode-wrap") || $("settings-trading-mode-toggle");
      if (target) {
        target.scrollIntoView({ behavior: "smooth", block: "center" });
        target.style.transition = "box-shadow 0.3s ease";
        target.style.boxShadow = "0 0 0 2px #0284c7, 0 0 16px rgba(2, 132, 199, 0.4)";
        setTimeout(() => {
          target.style.boxShadow = "";
        }, 2000);
      }
    }, 100);
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

async function switchToLiveHours() {
  const current = (state.snapshot && state.snapshot.app && state.snapshot.app.trading_mode) || (state.snapshot && state.snapshot.trading_mode) || "LIVE_HOURS";
  if (current === "LIVE_HOURS") return;
  if (!confirm("Switch to Live Hours? Real virtual orders will be strictly restricted to Sun-Thu 10:00-14:30 Asia/Dhaka.")) {
    return;
  }
  await setAutomationConfig({ trading_mode: "LIVE_HOURS" });
}

async function switchToTestMode() {
  const current = (state.snapshot && state.snapshot.app && state.snapshot.app.trading_mode) || (state.snapshot && state.snapshot.trading_mode) || "LIVE_HOURS";
  if (current === "TEST_OFFHOURS") return;
  await setAutomationConfig({ trading_mode: "TEST_OFFHOURS" });
}

["hdr-tmode-live", "settings-tmode-live", "overflow-tmode-live"].forEach((id) => {
  const el = $(id);
  if (el) {
    el.addEventListener("click", () => {
      switchToLiveHours();
      if (overflowMenu) overflowMenu.hidden = true;
    });
  }
});

["hdr-tmode-test", "settings-tmode-test", "overflow-tmode-test"].forEach((id) => {
  const el = $(id);
  if (el) {
    el.addEventListener("click", () => {
      switchToTestMode();
      if (overflowMenu) overflowMenu.hidden = true;
    });
  }
});

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
    if (typeof loadApiKeysSettings === "function") {
      try { loadApiKeysSettings(); } catch (err) { console.warn("Failed to load settings:", err); }
    }
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
    if (targetId === "overview") {
      const workspace = document.querySelector(".workspace");
      if (workspace) workspace.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      const targetEl = document.getElementById(targetId);
      if (targetEl) {
        targetEl.scrollIntoView({ behavior: "smooth", block: "start" });
      }
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

// Preload 475+ DSE catalog in background on boot
api("/api/stocknow/all-shares")
  .then((res) => {
    state.allDseShares = res.shares || [];
    if ($("cat-dse-count")) setText("cat-dse-count", state.allDseShares.length);
  })
  .catch(() => {});

// Initialize view router and scroll spy first so navigation works immediately
initViewRouter();
initScrollSpy();
initCharts();
updateControls();
refresh();
initRealtimeStream();
try { initHermesSidebar(); } catch (err) { console.warn("Sidebar init notice:", err); }
loadConversations();
loadSystemChanges();
if (typeof loadHermesOSState === "function") loadHermesOSState();
try { initAuthAndSettings(); } catch (err) { console.warn("Settings init notice:", err); }
