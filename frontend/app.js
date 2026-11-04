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

function setText(id, text) { $(id).textContent = String(text); }

function setPnl(id, value, asPercentage = false) {
  const node = $(id);
  node.textContent = asPercentage ? percentage(value) : currency(value, true);
  node.classList.toggle("positive", value >= 0);
  node.classList.toggle("negative", value < 0);
}

function tone(action) {
  if (/CRASH|BLOCKED|INVALID|STALE/.test(action)) return "negative";
  if (/BUY_ZONE|^BUY$|SELL_TIER|^SELL$|MATURE/.test(action)) return "positive";
  if (/PULLBACK|RECOVERY|LOCK|LOSS|DISABLED|ODD/.test(action)) return "amber";
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
  $("toast").textContent = message;
  $("toast").classList.toggle("error", error);
  $("toast").hidden = false;
  state.toastTimer = setTimeout(() => { $("toast").hidden = true; }, 5500);
}

function showError(message, withToast = true) {
  setText("error-text", message);
  $("error-banner").hidden = false;
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
      method, headers: requestHeaders, body: body === undefined ? undefined : JSON.stringify(body),
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
    setText("pause-button", paused ? "Resume engine" : "Pause engine");
    $("pause-button").classList.toggle("pause-active", paused);
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
    left.append(details);
    const value = element("div", "bucket-value", currency(bucket.available_cash));
    value.append(element("span", "", "SETTLED CASH"));
    card.append(left, value);
    return card;
  });
  $("bucket-stack").replaceChildren(...cards);
}

function smoothCurvePath(points) {
  if (!points || points.length === 0) return "";
  if (points.length === 1) return `M ${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`;
  if (points.length === 2) {
    return `M ${points[0].x.toFixed(2)},${points[0].y.toFixed(2)} L ${points[1].x.toFixed(2)},${points[1].y.toFixed(2)}`;
  }
  let d = `M ${points[0].x.toFixed(2)},${points[0].y.toFixed(2)}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i === 0 ? 0 : i - 1];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2 < points.length ? i + 2 : points.length - 1];

    const cp1x = p1.x + (p2.x - p0.x) / 6;
    const cp1y = p1.y + (p2.y - p0.y) / 6;
    const cp2x = p2.x - (p3.x - p1.x) / 6;
    const cp2y = p2.y - (p3.y - p1.y) / 6;

    d += ` C ${cp1x.toFixed(2)},${cp1y.toFixed(2)} ${cp2x.toFixed(2)},${cp2y.toFixed(2)} ${p2.x.toFixed(2)},${p2.y.toFixed(2)}`;
  }
  return d;
}

function renderMainChart() {
  const points = state.snapshot.normalized_curve;
  if (points.length < 2) {
    $("main-chart").replaceChildren(element("span", "muted", "Insufficient valid history to chart."));
    return;
  }
  setText("curve-sessions", `${points.length} sessions`);
  const last = points[points.length - 1].value;
  setText("index-value", last.toFixed(2));
  const change = (last / points[0].value - 1) * 100;
  setText("index-change", percentage(change));
  $("index-change").classList.toggle("positive", change >= 0);
  $("index-change").classList.toggle("negative", change < 0);
  const width = 700, height = 175, left = 36, right = 12, top = 10, bottom = 28;
  const chartW = width - left - right;
  const chartH = height - top - bottom;
  const values = points.map((point) => point.value);
  const min = Math.min(...values) - 1, max = Math.max(...values) + 1;
  const x = (i) => left + (i / (points.length - 1)) * chartW;
  const y = (value) => top + ((max - value) / (max - min)) * chartH;
  const svg = svgElement("svg", { viewBox: `0 0 ${width} ${height}`, preserveAspectRatio: "none", role: "img", "aria-label": "Synthetic normalized watchlist price index. Not portfolio performance." });
  const defs = svgElement("defs");
  const gradient = svgElement("linearGradient", { id: "chart-gradient", x1: "0", x2: "0", y1: "0", y2: "1" });
  gradient.append(svgElement("stop", { offset: "0%", "stop-color": "#5de4c7", "stop-opacity": ".18" }), svgElement("stop", { offset: "100%", "stop-color": "#5de4c7", "stop-opacity": "0" }));
  defs.append(gradient); svg.append(defs);
  for (let i = 0; i < 4; i += 1) {
    const value = min + ((max - min) * i) / 3;
    svg.append(svgElement("line", { x1: left, y1: y(value), x2: width - right, y2: y(value), class: "chart-grid" }));
    const label = svgElement("text", { x: left - 8, y: y(value) + 3, "text-anchor": "end", class: "chart-axis-label" });
    label.textContent = value.toFixed(1); svg.append(label);
  }
  const coords = points.map((pt, i) => ({ x: x(i), y: y(pt.value) }));
  const smoothPath = smoothCurvePath(coords);
  svg.append(svgElement("path", { d: `${smoothPath} L${x(points.length - 1)},${height - bottom} L${left},${height - bottom} Z`, class: "chart-area" }));
  svg.append(svgElement("path", { d: smoothPath, class: "chart-line" }));

  [...new Set([0, Math.floor((points.length - 1) / 2), points.length - 1])].forEach((i) => {
    const label = svgElement("text", { x: x(i), y: height - 5, "text-anchor": i === 0 ? "start" : i === points.length - 1 ? "end" : "middle", class: "chart-axis-label" });
    label.textContent = sessionDate(points[i].date, true); svg.append(label);
  });

  // Interactive Crosshair Elements (No static dots on the curve line - 100% clean curve)
  const crosshairV = svgElement("line", { x1: 0, y1: top, x2: 0, y2: height - bottom, class: "chart-crosshair-line", style: "display:none;" });
  const crosshairH = svgElement("line", { x1: left, y1: 0, x2: width - right, y2: 0, class: "chart-crosshair-line", style: "display:none;" });
  const crosshairDot = svgElement("circle", { cx: 0, cy: 0, r: 4, class: "chart-crosshair-point", style: "display:none;" });
  svg.append(crosshairV, crosshairH, crosshairDot);

  // Mouse overlay rect for continuous TradingView-style hover tracking
  const overlay = svgElement("rect", {
    x: left,
    y: top,
    width: chartW,
    height: chartH,
    fill: "transparent",
    style: "cursor: crosshair;",
  });

  overlay.addEventListener("mousemove", (e) => {
    const chartContainer = $("main-chart");
    if (!chartContainer) return;
    const rect = chartContainer.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const normX = Math.max(0, Math.min(chartW, mouseX - left));
    const t = normX / chartW;
    const continuousIdx = t * (points.length - 1);
    const i0 = Math.floor(continuousIdx);
    const i1 = Math.min(points.length - 1, i0 + 1);
    const frac = continuousIdx - i0;
    const interpolatedVal = points[i0].value + frac * (points[i1].value - points[i0].value);

    const ptX = left + normX;
    const ptY = y(interpolatedVal);

    crosshairV.setAttribute("x1", ptX);
    crosshairV.setAttribute("x2", ptX);
    crosshairV.style.display = "block";

    crosshairH.setAttribute("y1", ptY);
    crosshairH.setAttribute("y2", ptY);
    crosshairH.style.display = "block";

    crosshairDot.setAttribute("cx", ptX);
    crosshairDot.setAttribute("cy", ptY);
    crosshairDot.style.display = "block";

    const closestIdx = Math.min(points.length - 1, Math.max(0, Math.round(continuousIdx)));
    const pt = points[closestIdx];

    const chgFromBase = ((interpolatedVal / points[0].value - 1) * 100);
    const dateTrades = allTrades.filter((t) => t.date === pt.date || t.trade_on === pt.date);
    let tradeNote = "";
    if (dateTrades.length) {
      tradeNote = `<div style="margin-top:4px;border-top:1px solid var(--soft-line);padding-top:3px;">
        ${dateTrades.map((t) => `<strong style="color:${t.side === "BUY" ? "#22c55e" : "#ef4444"}">${t.side}</strong> ${t.symbol} ${t.quantity} qty @ ৳${t.price}`).join("<br>")}
      </div>`;
    }

    const tooltip = $("main-chart-tooltip");
    if (tooltip) {
      tooltip.innerHTML = `
        <div style="font-weight:700;color:var(--teal);">${sessionDate(pt.date)}</div>
        <div style="font-size:11px;font-weight:600;margin-top:2px;">Rebased: ${interpolatedVal.toFixed(2)} (${chgFromBase >= 0 ? "+" : ""}${chgFromBase.toFixed(2)}%)</div>
        ${tradeNote}
      `;
      tooltip.hidden = false;
      tooltip.style.left = `${Math.min(rect.width - 90, Math.max(90, ptX))}px`;
      tooltip.style.top = `${Math.max(20, ptY - 10)}px`;
    }
  });

  overlay.addEventListener("mouseleave", () => {
    crosshairV.style.display = "none";
    crosshairH.style.display = "none";
    crosshairDot.style.display = "none";
    const tooltip = $("main-chart-tooltip");
    if (tooltip) tooltip.hidden = true;
  });

  svg.append(overlay);
  $("main-chart").replaceChildren(svg);
}

function sparkline(history) {
  const values = history.map((point) => Number(point.close));
  if (values.length < 2 || values.some((value) => !Number.isFinite(value) || value <= 0)) return element("span", "muted small", "Invalid data");
  const low = Math.min(...values), high = Math.max(...values);
  const coords = values.map((val, i) => ({
    x: 2 + (i / (values.length - 1)) * 92,
    y: 25 - ((val - low) / (high - low || 1)) * 22,
  }));
  const path = smoothCurvePath(coords);
  const svg = svgElement("svg", { viewBox: "0 0 96 28", class: "sparkline", role: "img", "aria-label": "Synthetic recent price curve" });
  svg.append(svgElement("path", { d: path, class: values[values.length - 1] >= values[0] ? "spark-up" : "spark-down", fill: "none" }));
  return svg;
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
    const signal = cell(); signal.append(badge(company.curve.signal)); signal.title = company.curve.reason;
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

// --- DSE Market Map & Squarified Treemap Layout ---
function squarify(children, rect) {
  if (!children || !children.length || rect.w <= 0 || rect.h <= 0) return [];
  const total = children.reduce((acc, c) => acc + Math.max(0.01, Number(c.turnover_cr) || 0.01), 0);
  if (total <= 0) return [];

  const scale = (rect.w * rect.h) / total;
  const values = children.map((c) => Math.max(0.01, (Number(c.turnover_cr) || 0.01) * scale));

  const results = [];

  function layoutRow(row, rowValues, currentRect) {
    const isHorizontal = currentRect.w >= currentRect.h;
    const rowSum = rowValues.reduce((a, b) => a + b, 0);
    const rowThickness = isHorizontal ? rowSum / currentRect.h : rowSum / currentRect.w;

    let offset = 0;
    for (let i = 0; i < row.length; i++) {
      const itemVal = rowValues[i];
      const itemLen = rowThickness > 0 ? itemVal / rowThickness : 0;
      if (isHorizontal) {
        results.push({
          data: row[i],
          x: currentRect.x,
          y: currentRect.y + offset,
          w: Math.max(0, rowThickness),
          h: Math.max(0, itemLen),
        });
        offset += itemLen;
      } else {
        results.push({
          data: row[i],
          x: currentRect.x + offset,
          y: currentRect.y,
          w: Math.max(0, itemLen),
          h: Math.max(0, rowThickness),
        });
        offset += itemLen;
      }
    }

    if (isHorizontal) {
      return {
        x: currentRect.x + rowThickness,
        y: currentRect.y,
        w: Math.max(0, currentRect.w - rowThickness),
        h: currentRect.h,
      };
    } else {
      return {
        x: currentRect.x,
        y: currentRect.y + rowThickness,
        w: currentRect.w,
        h: Math.max(0, currentRect.h - rowThickness),
      };
    }
  }

  function worst(rowValues, length) {
    if (!rowValues.length || length <= 0) return Infinity;
    const s = rowValues.reduce((a, b) => a + b, 0);
    const maxVal = Math.max(...rowValues);
    const minVal = Math.min(...rowValues);
    const s2 = s * s;
    const l2 = length * length;
    return Math.max((l2 * maxVal) / s2, s2 / (l2 * minVal));
  }

  let currentRect = { ...rect };
  let currentRow = [];
  let currentRowValues = [];

  for (let i = 0; i < children.length; i++) {
    const child = children[i];
    const val = values[i];
    const length = Math.min(currentRect.w, currentRect.h);

    const testRow = [...currentRowValues, val];
    if (currentRow.length === 0 || worst(testRow, length) <= worst(currentRowValues, length)) {
      currentRow.push(child);
      currentRowValues.push(val);
    } else {
      currentRect = layoutRow(currentRow, currentRowValues, currentRect);
      currentRow = [child];
      currentRowValues = [val];
    }
  }

  if (currentRow.length > 0) {
    layoutRow(currentRow, currentRowValues, currentRect);
  }

  return results;
}

function showTreemapTooltip(e, contentHtml) {
  const tooltip = $("treemap-tooltip");
  const container = $("treemap-container");
  if (!tooltip || !container) return;
  tooltip.innerHTML = contentHtml;
  tooltip.hidden = false;
  const rect = container.getBoundingClientRect();
  const x = e.clientX - rect.left;
  const y = e.clientY - rect.top;
  tooltip.style.left = `${Math.min(rect.width - 90, Math.max(90, x))}px`;
  tooltip.style.top = `${Math.max(40, y)}px`;
}

function hideTreemapTooltip() {
  const tooltip = $("treemap-tooltip");
  if (tooltip) tooltip.hidden = true;
}

function renderMarketMap() {
  const container = $("treemap-container");
  if (!container || !state.snapshot || !state.snapshot.market_map) return;

  const mm = state.snapshot.market_map;
  const sectors = mm.treemap || [];
  const backBtn = $("treemap-back-btn");
  const activeView = $("treemap-active-view");

  const sectorSelect = $("treemap-sector-select");
  if (sectorSelect && sectorSelect.options.length <= 1) {
    sectors.forEach((s) => {
      const opt = element("option", "", s.name);
      opt.value = s.name;
      sectorSelect.append(opt);
    });
  }
  if (sectorSelect) {
    sectorSelect.value = state.activeSector || "ALL";
  }

  setText("treemap-turnover-badge", `Turnover: ${mm.total_turnover_cr} cr`);

  const width = container.clientWidth || 920;
  const height = 520;

  container.innerHTML = "";

  if (state.activeSector) {
    // Single Sector Drilldown View (matching Screenshot 2)
    const sector = sectors.find((s) => s.name === state.activeSector);
    if (!sector) {
      state.activeSector = null;
      renderMarketMap();
      return;
    }

    if (backBtn) backBtn.style.display = "inline-flex";
    if (activeView) setText("treemap-active-view", `${sector.name} (${sector.turnover_cr} cr)`);

    const drillHeader = element("div", "treemap-drill-header", sector.name);
    container.append(drillHeader);

    const contentHeight = height - 26;
    const tiles = squarify(sector.companies, { x: 0, y: 26, w: width, h: contentHeight });

    tiles.forEach((t) => {
      const c = t.data;
      const tile = element("div", "treemap-tile");
      tile.style.left = `${t.x.toFixed(1)}px`;
      tile.style.top = `${t.y.toFixed(1)}px`;
      tile.style.width = `${Math.max(0, t.w - 1).toFixed(1)}px`;
      tile.style.height = `${Math.max(0, t.h - 1).toFixed(1)}px`;

      if (c.change > 0) {
        tile.classList.add("tile-up");
        if (c.change >= 3.0) tile.classList.add("tile-strong", "finviz-glow-up");
      } else if (c.change < 0) {
        tile.classList.add("tile-down");
        if (c.change <= -2.0) tile.classList.add("finviz-glow-down");
      } else {
        tile.classList.add("tile-eql");
      }

      if (t.w < 65 || t.h < 45) tile.classList.add("tile-small");
      if (t.w < 45 || t.h < 32) tile.classList.add("tile-tiny");

      tile.append(
        element("span", "tile-symbol", c.symbol),
        element("span", "tile-change", `${c.change > 0 ? "+" : ""}${c.change.toFixed(2)}%`),
        element("span", "tile-turnover", `${c.turnover_cr.toFixed(2)}cr`)
      );

      tile.addEventListener("mousemove", (e) => {
        showTreemapTooltip(
          e,
          `<div class="tt-title">${sector.name}</div>
           <div class="tt-row"><strong style="color:#fff;">${c.symbol}</strong> <span>৳${c.price}</span></div>
           <div class="tt-row"><span class="tt-bullet" style="background:${c.change > 0 ? "#22c55e" : c.change < 0 ? "#ef4444" : "#3b82f6"}"></span> ${c.change > 0 ? "+" : ""}${c.change.toFixed(2)}% · ${c.turnover_cr.toFixed(2)}cr turnover</div>
           <div class="tt-row muted small" style="margin-top:3px;">Click to view Deep Trend & Profile ↗</div>`
        );
      });
      tile.addEventListener("mouseleave", hideTreemapTooltip);

      // In single sector drilldown, clicking tile opens Deep Trend modal
      tile.addEventListener("click", () => {
        openDeepTrendModal(c.symbol);
      });

      container.append(tile);
    });
  } else {
    // All Sectors View (matching Screenshot 1)
    if (backBtn) backBtn.style.display = "none";
    if (activeView) setText("treemap-active-view", "All Sectors");

    const sectorRects = squarify(sectors, { x: 0, y: 0, w: width, h: height });

    sectorRects.forEach((sr) => {
      const sector = sr.data;
      const sectorBox = element("div", "treemap-sector-group");
      sectorBox.style.left = `${sr.x.toFixed(1)}px`;
      sectorBox.style.top = `${sr.y.toFixed(1)}px`;
      sectorBox.style.width = `${Math.max(0, sr.w).toFixed(1)}px`;
      sectorBox.style.height = `${Math.max(0, sr.h).toFixed(1)}px`;

      const headerHeight = sr.h > 40 ? 20 : 0;
      if (headerHeight > 0) {
        const header = element("div", "treemap-sector-header", sector.name);
        header.title = `Click to drill into ${sector.name} (${sector.turnover_cr} cr)`;
        header.addEventListener("click", () => {
          state.activeSector = sector.name;
          renderMarketMap();
        });
        sectorBox.append(header);
      }

      const compHeight = Math.max(0, sr.h - headerHeight);
      const compTiles = squarify(sector.companies, { x: 0, y: headerHeight, w: sr.w, h: compHeight });

      compTiles.forEach((ct) => {
        const c = ct.data;
        const tile = element("div", "treemap-tile");
        tile.style.left = `${ct.x.toFixed(1)}px`;
        tile.style.top = `${ct.y.toFixed(1)}px`;
        tile.style.width = `${Math.max(0, ct.w - 1).toFixed(1)}px`;
        tile.style.height = `${Math.max(0, ct.h - 1).toFixed(1)}px`;

        if (c.change > 0) {
          tile.classList.add("tile-up");
          if (c.change >= 3.0) tile.classList.add("tile-strong", "finviz-glow-up");
        } else if (c.change < 0) {
          tile.classList.add("tile-down");
          if (c.change <= -2.0) tile.classList.add("finviz-glow-down");
        } else {
          tile.classList.add("tile-eql");
        }

        if (ct.w < 65 || ct.h < 45) tile.classList.add("tile-small");
        if (ct.w < 45 || ct.h < 32) tile.classList.add("tile-tiny");

        tile.append(
          element("span", "tile-symbol", c.symbol),
          element("span", "tile-change", `${c.change > 0 ? "+" : ""}${c.change.toFixed(2)}%`),
          element("span", "tile-turnover", `${c.turnover_cr.toFixed(2)}cr`)
        );

        tile.addEventListener("mousemove", (e) => {
          showTreemapTooltip(
            e,
            `<div class="tt-title">${sector.name}</div>
             <div class="tt-row"><strong style="color:#fff;">${c.symbol}</strong> <span>৳${c.price}</span></div>
             <div class="tt-row"><span class="tt-bullet" style="background:${c.change > 0 ? "#22c55e" : c.change < 0 ? "#ef4444" : "#3b82f6"}"></span> ${c.change > 0 ? "+" : ""}${c.change.toFixed(2)}% · ${c.turnover_cr.toFixed(2)}cr</div>
             <div class="tt-row muted">Sector total: ${sector.turnover_cr} cr</div>`
          );
        });
        tile.addEventListener("mouseleave", hideTreemapTooltip);

        tile.addEventListener("click", () => {
          state.activeSector = sector.name;
          renderMarketMap();
        });

        sectorBox.append(tile);
      });

      container.append(sectorBox);
    });
  }
}

function renderTopSectorsChart() {
  const svg = $("sector-gainer-chart");
  if (!svg || !state.snapshot || !state.snapshot.market_map) return;

  const data = state.snapshot.market_map.top_sectors_by_gainer || [];
  if (!data.length) return;

  svg.innerHTML = "";

  const width = 940;
  const height = 330;
  const left = 45;
  const right = 20;
  const top = 25;
  const bottom = 125;

  const chartW = width - left - right;
  const chartH = height - top - bottom;

  const maxY = Math.max(25, ...data.map((d) => d.total));

  // Background gridlines and Y-axis labels
  const gridSteps = 5;
  for (let i = 0; i <= gridSteps; i++) {
    const val = Math.round((maxY / gridSteps) * i);
    const y = top + chartH - (val / maxY) * chartH;

    const line = svgElement("line", {
      x1: left,
      y1: y.toFixed(1),
      x2: width - right,
      y2: y.toFixed(1),
      class: "gainer-grid",
    });
    svg.append(line);

    const txt = svgElement("text", {
      x: left - 8,
      y: (y + 3).toFixed(1),
      "text-anchor": "end",
      class: "gainer-label",
    });
    txt.textContent = String(val);
    svg.append(txt);
  }

  // Baseline axis
  svg.append(
    svgElement("line", {
      x1: left,
      y1: top + chartH,
      x2: width - right,
      y2: top + chartH,
      class: "gainer-axis",
    })
  );

  const step = chartW / data.length;
  const barW = Math.min(26, step * 0.72);

  data.forEach((d, idx) => {
    const barX = left + idx * step + (step - barW) / 2;

    const hUp = (d.up / maxY) * chartH;
    const hDown = (d.down / maxY) * chartH;
    const hEql = (d.eql / maxY) * chartH;

    const yUp = top + chartH - hUp;
    const yDown = yUp - hDown;
    const yEql = yDown - hEql;

    const group = svgElement("g", { class: "gainer-bar-segment" });

    // Up segment (bottom, green #22c55e)
    if (hUp > 0) {
      group.append(
        svgElement("rect", {
          x: barX.toFixed(1),
          y: yUp.toFixed(1),
          width: barW.toFixed(1),
          height: hUp.toFixed(1),
          fill: "#22c55e",
          rx: hDown === 0 && hEql === 0 ? "2" : "0",
        })
      );
    }

    // Down segment (middle, red #ef4444)
    if (hDown > 0) {
      group.append(
        svgElement("rect", {
          x: barX.toFixed(1),
          y: yDown.toFixed(1),
          width: barW.toFixed(1),
          height: hDown.toFixed(1),
          fill: "#ef4444",
          rx: hEql === 0 ? "2" : "0",
        })
      );
    }

    // Eql segment (top, blue #5b5bd6)
    if (hEql > 0) {
      group.append(
        svgElement("rect", {
          x: barX.toFixed(1),
          y: yEql.toFixed(1),
          width: barW.toFixed(1),
          height: hEql.toFixed(1),
          fill: "#5b5bd6",
          rx: "2",
        })
      );
    }

    // Interactive tooltip on bar hover
    group.addEventListener("mousemove", (e) => {
      showTreemapTooltip(
        e,
        `<div class="tt-title">${d.sector}</div>
         <div class="tt-row"><span class="tt-bullet" style="background:#22c55e"></span> Up: <strong>${d.up}</strong></div>
         <div class="tt-row"><span class="tt-bullet" style="background:#ef4444"></span> Down: <strong>${d.down}</strong></div>
         <div class="tt-row"><span class="tt-bullet" style="background:#5b5bd6"></span> Eql: <strong>${d.eql}</strong></div>
         <div class="tt-row muted">Turnover: ${d.turnover_cr} cr (${d.total} companies)</div>`
      );
    });
    group.addEventListener("mouseleave", hideTreemapTooltip);

    // Clicking a bar drills down into that sector on the treemap
    group.addEventListener("click", () => {
      state.activeSector = d.sector;
      renderMarketMap();
      const treemapElem = $("market-map");
      if (treemapElem) treemapElem.scrollIntoView({ behavior: "smooth" });
    });

    svg.append(group);

    // Rotated Sector Label along X axis
    const labelX = (barX + barW / 2).toFixed(1);
    const labelY = (top + chartH + 12).toFixed(1);

    const text = svgElement("text", {
      transform: `translate(${labelX}, ${labelY}) rotate(-90)`,
      "text-anchor": "end",
      class: "gainer-label",
    });
    text.textContent = d.sector;
    text.style.cursor = "pointer";
    text.addEventListener("click", () => {
      state.activeSector = d.sector;
      renderMarketMap();
      const treemapElem = $("market-map");
      if (treemapElem) treemapElem.scrollIntoView({ behavior: "smooth" });
    });
    svg.append(text);
  });
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

function renderHermesSkills() {
  const hermes = state.snapshot.hermes;
  if (!hermes) return;
  const skills = hermes.skills || [];
  if ($("skills-count")) setText("skills-count", skills.length);

  const skillsList = $("skills-list");
  if (skillsList) {
    const skillCards = skills.map((s) => {
      const card = element("div", "skill-card");
      const top = element("div", "skill-card-top");
      top.append(element("strong", "", s.title));
      top.append(element("span", "skill-rev", `v${s.version} · ${s.revision_count} patches`));
      const tags = element("div", "skill-tags");
      s.tags.forEach((t) => tags.append(element("span", "skill-tag", t)));
      card.append(top, tags);
      return card;
    });
    skillsList.replaceChildren(...skillCards);
  }

  const factsList = $("durable-facts-list");
  if (factsList) {
    const facts = hermes.durable_facts || [];
    const factCards = facts.map((f) => {
      const item = element("div", "fact-item");
      item.append(element("strong", "", f.symbol), element("span", "muted", `[${f.category}] `), document.createTextNode(f.fact));
      return item;
    });
    factsList.replaceChildren(...(factCards.length ? factCards : [element("div", "muted small", "No company facts recorded yet.")]));
  }

  const cpList = $("checkpoints-list");
  if (cpList) {
    const checkpoints = hermes.checkpoints || [];
    const cpItems = checkpoints.map((cp) => {
      const item = element("div", `checkpoint-item ${cp.reverted ? "cp-reverted" : ""}`);
      item.append(element("strong", "", cp.action), element("span", "", cp.description.slice(0, 45) + "..."));
      return item;
    });
    cpList.replaceChildren(...(cpItems.length ? cpItems : [element("div", "muted small", "No checkpoints recorded yet.")]));
  }
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
    row.append(cell(sessionDate(trade.date, true)), company, side, cell(trade.quantity, "align-right"), cell(numberFormat.format(trade.price), "align-right"), cell(numberFormat.format(trade.fee), "align-right"), cell(trade.side === "SELL" ? `${trade.realized_pnl >= 0 ? "+" : ""}${numberFormat.format(trade.realized_pnl)}` : "—", `align-right ${trade.side === "SELL" ? "positive" : "muted"}`), settlement);
    return row;
  });
  if (!rows.length) { const row = element("tr"); const td = cell("No trades in this accounting period.", "loading-cell"); td.colSpan = 8; row.append(td); rows.push(row); }
  $("trades-body").replaceChildren(...rows);
  setText("ledger-range", `${sessionDate(period.start, true)} – ${sessionDate(period.end, true)} · Latest 100 records shown; totals use full ledger.`);
}

function addMessage(role, content, provider = null) {
  const article = element("article", `chat-message ${role}`);
  const author = element("div", "message-author");
  if (role === "assistant") author.append(element("span", "assistant-avatar", "✦"));
  author.append(document.createTextNode(role === "user" ? "YOU" : "HERMES"));
  if (provider) author.append(element("span", "muted", `· ${provider.toUpperCase()}`));
  const body = element("div", "message-body", content); // No HTML/Markdown execution.
  article.append(author, body);
  $("chat-messages").append(article);
  $("chat-messages").scrollTop = $("chat-messages").scrollHeight;
  return article;
}

async function sendChat(message) {
  message = message.trim();
  if (!message || message.length > 2000 || state.chatBusy || !state.snapshot) return;
  const history = state.history.slice(-8).map((turn) => ({ ...turn, content: turn.content.slice(0, 2000) }));
  addMessage("user", message);
  state.history.push({ role: "user", content: message });
  $("chat-input").value = "";
  state.chatBusy = true; updateControls();
  const thinking = addMessage("assistant", "Reading the current paper portfolio…");
  thinking.querySelector(".message-body").classList.add("thinking");
  try {
    const payload = {
      message,
      history,
      conversation_id: state.activeConversationId || undefined,
    };
    const response = await api("/api/chat", { method: "POST", body: payload, timeout: 35000 });
    thinking.remove();
    const article = addMessage("assistant", response.reply, response.provider === "local" ? "local summary" : "OpenRouter");
    if (response.warning) article.append(element("p", "response-warning", response.warning));
    state.lastChatProvider = response.provider;
    setText("chat-provider", response.provider === "local" ? "LOCAL SUMMARY · NO API COST FOR THIS REPLY" : `OPENROUTER · ${response.model}`);
    setText("chat-footer-note", response.provider === "local" ? "Read-only local summary. No trade or rule changes made." : "External AI used demo portfolio context. No execution tools.");
    state.history.push({ role: "assistant", content: response.reply.slice(0, 2000) });
    state.history = state.history.slice(-8);

    if (response.conversation_id && !state.activeConversationId) {
      state.activeConversationId = response.conversation_id;
      localStorage.setItem("humming-bird-active-conv-id", response.conversation_id);
    }

    if (response.agentic_action) {
      await refresh(true);
      notify(`Hermes action: ${response.agentic_action.replaceAll("_", " ")} executed.`);
      loadSystemChanges();
    }
    $("chat-messages").scrollTop = $("chat-messages").scrollHeight;
  } catch (error) {
    thinking.remove();
    addMessage("assistant", `Unable to get a response: ${error.message}\nNo trade or settings change was made.`, "request error");
  } finally { state.chatBusy = false; updateControls(); $("chat-input").focus(); }
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

// --- "What-If" Profit Simulator Logic ---
function updateWhatIfSimulator(company) {
  if (!company) {
    company = (state.snapshot && state.snapshot.companies)
      ? state.snapshot.companies.find((c) => c.symbol === state.selectedSymbol)
      : null;
  }
  if (!company) return;

  const slider = $("what-if-slider");
  const deltaPct = slider ? Number(slider.value) : 0;
  const currentPrice = Number(company.price);
  const targetPrice = currentPrice * (1 + deltaPct / 100);

  const matureQty = company.mature_qty || company.holding_qty || 100;
  const costBasis = (company.cost_basis && company.holding_qty)
    ? (company.cost_basis / company.holding_qty) * matureQty
    : currentPrice * matureQty;

  const grossExit = targetPrice * matureQty;
  const buyFee = costBasis * 0.005;
  const sellFee = grossExit * 0.005;
  const totalFees = buyFee + sellFee;
  const netProfit = grossExit - costBasis - totalFees;
  const netReturnPct = costBasis > 0 ? (netProfit / costBasis) * 100 : 0;

  if ($("sim-symbol-badge")) setText("sim-symbol-badge", `${company.symbol} (${matureQty} sh)`);
  if ($("what-if-target-price")) setText("what-if-target-price", `৳${targetPrice.toFixed(2)}`);
  if ($("what-if-target-pct")) {
    setText("what-if-target-pct", `${deltaPct >= 0 ? "+" : ""}${deltaPct.toFixed(2)}%`);
    $("what-if-target-pct").className = deltaPct >= 0 ? "positive" : "negative";
  }

  if ($("what-if-gross")) setText("what-if-gross", currency(grossExit));
  if ($("what-if-fee")) setText("what-if-fee", currency(totalFees));
  if ($("what-if-net-pnl")) {
    setText("what-if-net-pnl", currency(netProfit, true));
    $("what-if-net-pnl").className = netProfit >= 0 ? "positive" : "negative";
  }
  if ($("what-if-return-pct")) {
    setText("what-if-return-pct", percentage(netReturnPct));
    $("what-if-return-pct").className = netReturnPct >= 0 ? "positive" : "negative";
  }
}

function updateModalSimulator(company) {
  if (!company) return;
  const slider = $("modal-sim-slider");
  const deltaPct = slider ? Number(slider.value) : 0;
  const currentPrice = Number(company.price);
  const targetPrice = currentPrice * (1 + deltaPct / 100);

  const matureQty = company.mature_qty || company.holding_qty || 100;
  const costBasis = (company.cost_basis && company.holding_qty)
    ? (company.cost_basis / company.holding_qty) * matureQty
    : currentPrice * matureQty;

  const grossExit = targetPrice * matureQty;
  const buyFee = costBasis * 0.005;
  const sellFee = grossExit * 0.005;
  const totalFees = buyFee + sellFee;
  const netProfit = grossExit - costBasis - totalFees;
  const netReturnPct = costBasis > 0 ? (netProfit / costBasis) * 100 : 0;

  if ($("modal-sim-name")) setText("modal-sim-name", `${company.symbol} (${matureQty} mature shares)`);
  if ($("modal-sim-target-price")) setText("modal-sim-target-price", `৳${targetPrice.toFixed(2)}`);
  if ($("modal-sim-target-pct")) {
    setText("modal-sim-target-pct", `${deltaPct >= 0 ? "+" : ""}${deltaPct.toFixed(2)}%`);
    $("modal-sim-target-pct").className = deltaPct >= 0 ? "positive" : "negative";
  }

  if ($("modal-sim-gross")) setText("modal-sim-gross", currency(grossExit));
  if ($("modal-sim-fee")) setText("modal-sim-fee", currency(totalFees));
  if ($("modal-sim-net-pnl")) {
    setText("modal-sim-net-pnl", currency(netProfit, true));
    $("modal-sim-net-pnl").className = netProfit >= 0 ? "positive" : "negative";
  }
  if ($("modal-sim-return-pct")) {
    setText("modal-sim-return-pct", percentage(netReturnPct));
    $("modal-sim-return-pct").className = netReturnPct >= 0 ? "positive" : "negative";
  }
}

// --- Individual Company Deep-Trend View & Fundamentals Modal ---
function openDeepTrendModal(symbol) {
  if (!state.snapshot || !state.snapshot.companies) return;
  const company = state.snapshot.companies.find((c) => c.symbol === symbol)
    || state.snapshot.companies[0];
  if (!company) return;

  state.deepCompany = company;
  const modal = $("deep-trend-modal");
  if (!modal) return;

  if ($("modal-company-title")) {
    setText("modal-company-title", `${company.symbol} `);
    const sub = element("span", "modal-company-sub", company.name);
    $("modal-company-title").append(sub);
  }

  if ($("modal-company-sector")) setText("modal-company-sector", company.sector.replaceAll("_", " "));
  const catCode = company.watchlist_category || "GSC";
  if ($("modal-company-category")) setText("modal-company-category", catLabels[catCode] || catCode);

  if ($("modal-price")) setText("modal-price", currency(company.price));
  const dayChg = (company.curve && company.curve.day_change_pct) || 0;
  if ($("modal-change")) {
    setText("modal-change", percentage(dayChg));
    $("modal-change").className = `modal-change ${dayChg >= 0 ? "positive" : "negative"}`;
  }

  const signal = (company.curve && company.curve.signal) || "MID_RANGE";
  if ($("modal-signal-tag")) {
    setText("modal-signal-tag", signal.replaceAll("_", " "));
    $("modal-signal-tag").className = `signal-badge tone-${tone(signal)}`;
  }

  const f = company.fundamentals || {};
  if ($("fund-pe")) setText("fund-pe", f.pe_ratio ? f.pe_ratio.toFixed(1) : "—");
  if ($("fund-eps")) setText("fund-eps", f.eps ? `৳${f.eps.toFixed(2)}` : "—");
  if ($("fund-nav")) setText("fund-nav", f.nav ? `৳${f.nav.toFixed(2)}` : "—");
  if ($("fund-mcap")) setText("fund-mcap", f.market_cap_cr ? `${numberFormat.format(f.market_cap_cr)} cr` : "—");
  if ($("fund-div")) setText("fund-div", f.dividend_yield ? `${f.dividend_yield.toFixed(1)}%` : "—");
  if ($("fund-paidup")) setText("fund-paidup", f.paid_up_capital_cr ? `${numberFormat.format(f.paid_up_capital_cr)} cr` : "—");
  if ($("fund-52w")) setText("fund-52w", f.low_52w && f.high_52w ? `৳${f.low_52w} — ৳${f.high_52w}` : "—");
  if ($("fund-cat")) setText("fund-cat", f.category ? `Category ${f.category} (${f.listing_year || "—"})` : "—");

  document.querySelectorAll("#deep-timeframe-tabs button").forEach((b) => {
    b.classList.toggle("active", b.dataset.tf === state.deepTimeframe);
  });

  renderDeepTrendChart(company, state.deepTimeframe);
  updateModalSimulator(company);

  if (typeof modal.showModal === "function") {
    modal.showModal();
  } else {
    modal.setAttribute("open", "");
  }
}

function closeDeepTrendModal() {
  const modal = $("deep-trend-modal");
  if (!modal) return;
  if (typeof modal.close === "function") {
    modal.close();
  } else {
    modal.removeAttribute("open");
  }
}

function renderDeepTrendChart(company, timeframe = "7d") {
  const mount = $("deep-trend-chart-mount");
  if (!mount || !company) return;

  const ext = company.extended_history || {};
  let series = ext[timeframe] || company.history || [];
  if (series.length < 2) series = company.history || [];
  if (series.length < 2) {
    mount.innerHTML = `<div class="muted small" style="display:grid;place-items:center;height:100%;">Insufficient historical curve points.</div>`;
    return;
  }

  const width = 880, height = 240, left = 55, right = 15, top = 20, bottom = 30;
  const chartW = width - left - right;
  const chartH = height - top - bottom;

  const closes = series.map((pt) => Number(pt.close));
  const support = Number(company.curve.support || company.curve.low || Math.min(...closes));
  const resistance = Number(company.curve.resistance || company.curve.high || Math.max(...closes));
  const buyCeiling = Number(company.curve.buy_zone_ceiling || support);

  if ($("deep-support-val")) setText("deep-support-val", `৳${support.toFixed(2)}`);
  if ($("deep-resistance-val")) setText("deep-resistance-val", `৳${resistance.toFixed(2)}`);

  const minVal = Math.min(...closes, support) * 0.985;
  const maxVal = Math.max(...closes, resistance) * 1.015;
  const range = maxVal - minVal || 1;

  const x = (i) => left + (i / (series.length - 1)) * chartW;
  const y = (val) => top + ((maxVal - val) / range) * chartH;

  const svg = svgElement("svg", {
    viewBox: `0 0 ${width} ${height}`,
    preserveAspectRatio: "none",
    class: "deep-trend-svg",
  });

  const defs = svgElement("defs");
  const grad = svgElement("linearGradient", { id: "deep-curve-grad", x1: "0", y1: "0", x2: "0", y2: "1" });
  grad.append(
    svgElement("stop", { offset: "0%", "stop-color": "#5de4c7", "stop-opacity": "0.22" }),
    svgElement("stop", { offset: "100%", "stop-color": "#5de4c7", "stop-opacity": "0" })
  );
  defs.append(grad);
  svg.append(defs);

  // Background Gridlines
  for (let step = 0; step <= 4; step++) {
    const val = minVal + (range * step) / 4;
    const yPos = y(val);
    svg.append(svgElement("line", { x1: left, y1: yPos, x2: width - right, y2: yPos, stroke: "var(--chart-grid)", "stroke-width": 1, "stroke-dasharray": "2 3" }));
    const lbl = svgElement("text", { x: left - 8, y: yPos + 3, "text-anchor": "end", fill: "var(--muted)", "font-size": 9.5 });
    lbl.textContent = `৳${val.toFixed(1)}`;
    svg.append(lbl);
  }

  // Shaded Buy Zone band: [support, buyCeiling]
  if (buyCeiling > support) {
    const yTop = Math.min(y(support), y(buyCeiling));
    const bandH = Math.abs(y(support) - y(buyCeiling));
    svg.append(svgElement("rect", {
      x: left,
      y: yTop,
      width: chartW,
      height: bandH,
      fill: "rgba(34, 197, 94, 0.08)",
      stroke: "none",
    }));
  }

  // Horizontal Support line (dashed green)
  svg.append(svgElement("line", {
    x1: left,
    y1: y(support),
    x2: width - right,
    y2: y(support),
    stroke: "#22c55e",
    "stroke-width": 1.5,
    "stroke-dasharray": "4 4",
  }));
  const supLbl = svgElement("text", { x: width - right - 4, y: y(support) - 4, "text-anchor": "end", fill: "#22c55e", "font-size": 9, "font-weight": 700 });
  supLbl.textContent = `SUPPORT ৳${support.toFixed(1)}`;
  svg.append(supLbl);

  // Horizontal Resistance line (dashed red)
  svg.append(svgElement("line", {
    x1: left,
    y1: y(resistance),
    x2: width - right,
    y2: y(resistance),
    stroke: "#ef4444",
    "stroke-width": 1.5,
    "stroke-dasharray": "4 4",
  }));
  const resLbl = svgElement("text", { x: width - right - 4, y: y(resistance) - 4, "text-anchor": "end", fill: "#ef4444", "font-size": 9, "font-weight": 700 });
  resLbl.textContent = `RESISTANCE ৳${resistance.toFixed(1)}`;
  svg.append(resLbl);

  // Price Area & Line with smooth cubic bezier curve
  const coords = series.map((pt, i) => ({ x: x(i), y: y(Number(pt.close)) }));
  const pathD = smoothCurvePath(coords);
  svg.append(svgElement("path", {
    d: `${pathD} L${x(series.length - 1).toFixed(1)},${(top + chartH).toFixed(1)} L${left},${(top + chartH).toFixed(1)} Z`,
    fill: "url(#deep-curve-grad)",
  }));
  svg.append(svgElement("path", {
    d: pathD,
    fill: "none",
    stroke: "var(--teal)",
    "stroke-width": 2.2,
  }));

  // X Axis Session Dates
  const sampleIndices = [...new Set([0, Math.floor((series.length - 1) / 3), Math.floor((series.length - 1) * 2 / 3), series.length - 1])];
  sampleIndices.forEach((idx) => {
    const xPos = x(idx);
    const dateLbl = svgElement("text", {
      x: xPos,
      y: height - 8,
      "text-anchor": idx === 0 ? "start" : idx === series.length - 1 ? "end" : "middle",
      fill: "var(--muted)",
      "font-size": 9.5,
    });
    dateLbl.textContent = sessionDate(series[idx].date, true);
    svg.append(dateLbl);
  });

  // Bot Order Markers (B = Buy in green, S = Sell in red)
  const companyTrades = (state.snapshot.trades || []).filter((t) => t.symbol === company.symbol);
  series.forEach((pt, idx) => {
    const tradesOnDate = companyTrades.filter((t) => t.date === pt.date || t.trade_on === pt.date);
    tradesOnDate.forEach((t) => {
      const isBuy = t.side === "BUY";
      const markerX = x(idx);
      const markerY = y(Number(pt.close));

      const markerG = svgElement("g", { class: "chart-trade-marker" });
      markerG.append(svgElement("circle", {
        cx: markerX,
        cy: markerY,
        r: 7,
        fill: isBuy ? "#16a34a" : "#dc2626",
        stroke: "#ffffff",
        "stroke-width": 1.5,
      }));
      const textM = svgElement("text", {
        x: markerX,
        y: markerY + 3.5,
        "text-anchor": "middle",
        fill: "#ffffff",
        "font-size": 8.5,
        "font-weight": 800,
      });
      textM.textContent = isBuy ? "B" : "S";
      markerG.append(textM);
      markerG.title = `${t.side} ${t.quantity} shares @ ৳${t.price} (${t.reason || ""})`;
      svg.append(markerG);
    });
  });

  // Crosshair vertical & horizontal lines & tracking dot
  const crosshairV = svgElement("line", { x1: 0, y1: top, x2: 0, y2: top + chartH, class: "chart-crosshair-line", style: "display:none;" });
  const crosshairH = svgElement("line", { x1: left, y1: 0, x2: width - right, y2: 0, class: "chart-crosshair-line", style: "display:none;" });
  const crosshairPoint = svgElement("circle", { cx: 0, cy: 0, r: 4, class: "chart-crosshair-point", style: "display:none;" });
  svg.append(crosshairV, crosshairH, crosshairPoint);

  // Overlay for mouse events
  const overlay = svgElement("rect", {
    x: left,
    y: top,
    width: chartW,
    height: chartH,
    fill: "transparent",
    style: "cursor: crosshair;",
  });

  overlay.addEventListener("mousemove", (e) => {
    const rect = mount.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const normX = Math.max(0, Math.min(chartW, mouseX - left));
    const t = normX / chartW;
    const continuousIdx = t * (series.length - 1);
    const i0 = Math.floor(continuousIdx);
    const i1 = Math.min(series.length - 1, i0 + 1);
    const frac = continuousIdx - i0;
    const val = Number(series[i0].close) + frac * (Number(series[i1].close) - Number(series[i0].close));

    const ptX = left + normX;
    const ptY = y(val);

    crosshairV.setAttribute("x1", ptX);
    crosshairV.setAttribute("x2", ptX);
    crosshairV.style.display = "block";

    crosshairH.setAttribute("y1", ptY);
    crosshairH.setAttribute("y2", ptY);
    crosshairH.style.display = "block";

    crosshairPoint.setAttribute("cx", ptX);
    crosshairPoint.setAttribute("cy", ptY);
    crosshairPoint.style.display = "block";

    const closestIdx = Math.min(series.length - 1, Math.max(0, Math.round(continuousIdx)));
    const pt = series[closestIdx];

    const chgFromStart = ((val / Number(series[0].close) - 1) * 100);
    const dateTrades = companyTrades.filter((t) => t.date === pt.date || t.trade_on === pt.date);
    let tradeNote = "";
    if (dateTrades.length) {
      tradeNote = `<div style="margin-top:4px;border-top:1px solid var(--soft-line);padding-top:3px;">
        ${dateTrades.map((t) => `<strong style="color:${t.side === "BUY" ? "#22c55e" : "#ef4444"}">${t.side}</strong> ${t.quantity} qty @ ৳${t.price}`).join("<br>")}
      </div>`;
    }

    const tooltip = $("deep-chart-tooltip");
    if (tooltip) {
      tooltip.innerHTML = `
        <div style="font-weight:700;color:var(--teal);">${sessionDate(pt.date)}</div>
        <div style="font-size:12px;font-weight:600;margin-top:2px;">Close: ৳${val.toFixed(2)} (${chgFromStart >= 0 ? "+" : ""}${chgFromStart.toFixed(2)}%)</div>
        ${tradeNote}
      `;
      tooltip.hidden = false;
      tooltip.style.left = `${Math.min(rect.width - 100, Math.max(100, ptX))}px`;
      tooltip.style.top = `${Math.max(30, ptY - 10)}px`;
    }
  });

  overlay.addEventListener("mouseleave", () => {
    crosshairV.style.display = "none";
    crosshairH.style.display = "none";
    crosshairPoint.style.display = "none";
    const tooltip = $("deep-chart-tooltip");
    if (tooltip) tooltip.hidden = true;
  });

  svg.append(overlay);
  mount.replaceChildren(svg);
}

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
if ($("open-deep-trend")) {
  $("open-deep-trend").addEventListener("click", () => openDeepTrendModal(state.selectedSymbol));
}
if ($("modal-close-btn")) {
  $("modal-close-btn").addEventListener("click", closeDeepTrendModal);
}
if ($("modal-backdrop")) {
  $("modal-backdrop").addEventListener("click", closeDeepTrendModal);
}
document.querySelectorAll("#deep-timeframe-tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    state.deepTimeframe = btn.dataset.tf;
    document.querySelectorAll("#deep-timeframe-tabs button").forEach((b) => b.classList.toggle("active", b === btn));
    if (state.deepCompany) renderDeepTrendChart(state.deepCompany, state.deepTimeframe);
  });
});

if ($("what-if-slider")) {
  $("what-if-slider").addEventListener("input", () => updateWhatIfSimulator());
}
if ($("modal-sim-slider")) {
  $("modal-sim-slider").addEventListener("input", () => {
    if (state.deepCompany) updateModalSimulator(state.deepCompany);
  });
}
if ($("treemap-sector-select")) {
  $("treemap-sector-select").addEventListener("change", (e) => {
    const val = e.target.value;
    state.activeSector = val === "ALL" ? null : val;
    renderMarketMap();
  });
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

  // Master switch
  const masterBtn = $("master-automation-toggle");
  if (masterBtn) {
    masterBtn.classList.toggle("is-active", enabled);
    masterBtn.classList.toggle("is-paused", !enabled);
    masterBtn.disabled = state.busy;
  }
  const statusText = $("master-automation-status-text");
  if (statusText) {
    statusText.textContent = enabled ? "AUTOMATION ON" : "AUTOMATION OFF";
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

  // Polling Interval Pills
  const intervalWrap = $("polling-interval-wrap");
  const isPollingActive = enabled && mode === "BACKGROUND_POLLING";
  if (intervalWrap) {
    intervalWrap.classList.toggle("disabled", !isPollingActive);
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

if ($("mode-btn-polling")) {
  $("mode-btn-polling").addEventListener("click", () => {
    if (!state.snapshot) return;
    const app = state.snapshot.app || {};
    const enabled = app.automation_enabled !== undefined ? Boolean(app.automation_enabled) : !app.paused;
    const interval = Number(app.polling_interval_sec || 120);
    setAutomationConfig({
      automation_enabled: enabled,
      ingestion_mode: "BACKGROUND_POLLING",
      polling_interval_sec: interval,
    });
  });
}

if ($("mode-btn-live")) {
  $("mode-btn-live").addEventListener("click", () => {
    if (!state.snapshot) return;
    const app = state.snapshot.app || {};
    const enabled = app.automation_enabled !== undefined ? Boolean(app.automation_enabled) : !app.paused;
    const interval = Number(app.polling_interval_sec || 120);
    setAutomationConfig({
      automation_enabled: enabled,
      ingestion_mode: "SIDE_BY_SIDE_LIVE",
      polling_interval_sec: interval,
    });
  });
}

document.querySelectorAll("#polling-interval-pills .pill-btn").forEach((pill) => {
  pill.addEventListener("click", () => {
    if (!state.snapshot) return;
    const app = state.snapshot.app || {};
    const enabled = app.automation_enabled !== undefined ? Boolean(app.automation_enabled) : !app.paused;
    const mode = app.ingestion_mode || "BACKGROUND_POLLING";
    const sec = Number(pill.dataset.sec);
    setAutomationConfig({
      automation_enabled: enabled,
      ingestion_mode: mode,
      polling_interval_sec: sec,
    });
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

// --- Hermes IDE Resizable Sidebar, Tabs & Antigravity History ---
function initHermesSidebar() {
  const sidebar = $("hermes-sidebar");
  const resizeHandle = $("hermes-resize-handle");
  const collapseBtn = $("hermes-collapse-btn");
  const openBtn = $("floating-hermes-open");
  const appShell = document.querySelector(".app-shell");

  // Restore saved width
  const savedWidth = localStorage.getItem("humming-bird-hermes-width");
  if (savedWidth) {
    const parsed = parseInt(savedWidth, 10);
    if (parsed >= 260 && parsed <= 700) {
      document.documentElement.style.setProperty("--hermes-width", `${parsed}px`);
    }
  }

  // Restore collapsed state
  const isCollapsed = localStorage.getItem("humming-bird-hermes-collapsed") === "true";
  if (isCollapsed && appShell && openBtn) {
    appShell.classList.add("hermes-collapsed");
    openBtn.hidden = false;
  }

  // Drag Resizing
  if (resizeHandle && appShell) {
    let isDragging = false;
    resizeHandle.addEventListener("mousedown", (e) => {
      isDragging = true;
      resizeHandle.classList.add("is-dragging");
      document.body.style.userSelect = "none";
      document.body.style.cursor = "col-resize";
    });

    window.addEventListener("mousemove", (e) => {
      if (!isDragging) return;
      const newWidth = Math.max(280, Math.min(650, window.innerWidth - e.clientX));
      document.documentElement.style.setProperty("--hermes-width", `${newWidth}px`);
      localStorage.setItem("humming-bird-hermes-width", newWidth);
    });

    window.addEventListener("mouseup", () => {
      if (isDragging) {
        isDragging = false;
        resizeHandle.classList.remove("is-dragging");
        document.body.style.userSelect = "";
        document.body.style.cursor = "";
      }
    });
  }

  // Collapse / Minimize
  if (collapseBtn && appShell && openBtn) {
    collapseBtn.addEventListener("click", () => {
      appShell.classList.add("hermes-collapsed");
      openBtn.hidden = false;
      localStorage.setItem("humming-bird-hermes-collapsed", "true");
    });
  }

  if (openBtn && appShell) {
    openBtn.addEventListener("click", () => {
      appShell.classList.remove("hermes-collapsed");
      openBtn.hidden = true;
      localStorage.setItem("humming-bird-hermes-collapsed", "false");
    });
  }

  // IDE Tabs
  const tabs = [
    { id: "tab-hermes-chat", paneId: "pane-hermes-chat" },
    { id: "tab-hermes-conversations", paneId: "pane-hermes-conversations", onOpen: loadConversations },
    { id: "tab-hermes-changes", paneId: "pane-hermes-changes", onOpen: loadSystemChanges },
    { id: "tab-hermes-skills", paneId: "pane-hermes-skills" },
  ];

  tabs.forEach(({ id, paneId, onOpen }) => {
    const tabEl = $(id);
    if (!tabEl) return;
    tabEl.addEventListener("click", () => {
      tabs.forEach((t) => {
        const b = $(t.id);
        const p = $(t.paneId);
        if (b) {
          b.classList.toggle("active", t.id === id);
          b.setAttribute("aria-selected", t.id === id ? "true" : "false");
        }
        if (p) {
          p.hidden = t.paneId !== paneId;
          p.classList.toggle("is-active", t.paneId === paneId);
        }
      });
      if (onOpen) onOpen();
    });
  });

  // Rollback buttons
  ["rollback-pane-btn", "rollback-skills-btn", "rollback-button"].forEach((btnId) => {
    const btn = $(btnId);
    if (btn) {
      btn.addEventListener("click", async () => {
        try {
          const res = await api("/api/hermes/rollback", { method: "POST" });
          await refresh(true);
          notify(`Rollback applied: ${res.action_reverted} (${res.description})`);
          loadSystemChanges();
        } catch (err) {
          notify(`Rollback failed: ${err.message}`, true);
        }
      });
    }
  });

  // New conversation button
  const newConvBtn = $("new-conversation-btn");
  if (newConvBtn) {
    newConvBtn.addEventListener("click", createNewConversation);
  }

  const refreshChangesBtn = $("refresh-changes-btn");
  if (refreshChangesBtn) {
    refreshChangesBtn.addEventListener("click", loadSystemChanges);
  }
}

// --- Conversations (Human Topic Separator) ---
state.activeConversationId = localStorage.getItem("humming-bird-active-conv-id") || null;

async function loadConversations() {
  const container = $("conversations-list");
  if (!container) return;
  try {
    const res = await api("/api/hermes/conversations");
    const threads = res.conversations || [];
    setText("conversations-badge", threads.length);
    if (threads.length === 0) {
      container.replaceChildren(element("div", "empty-state-small", "No conversation topics yet. Start one!"));
      return;
    }
    const items = threads.map((thread) => {
      const item = element("div", `conversation-item ${thread.id === state.activeConversationId ? "active" : ""}`);
      const topRow = element("div", "conv-top-row");
      const title = element("strong", "conv-title", thread.title || "Untitled Conversation");
      const time = element("span", "conv-time", formatRelativeTime(thread.updated_at));
      topRow.append(title, time);

      const sub = element("div", "conv-sub");
      sub.append(
        element("span", "", `${thread.message_count} turns`),
        element("span", "muted", "· Shared memory")
      );

      item.append(topRow, sub);
      item.addEventListener("click", () => switchConversation(thread));
      return item;
    });
    container.replaceChildren(...items);
  } catch (err) {
    container.replaceChildren(element("div", "empty-state-small", `Failed to load topics: ${err.message}`));
  }
}

async function switchConversation(thread) {
  state.activeConversationId = thread.id;
  localStorage.setItem("humming-bird-active-conv-id", thread.id);
  setText("active-conv-title", thread.title);

  // Switch to Chat tab
  const chatTab = $("tab-hermes-chat");
  if (chatTab) chatTab.click();

  // Load thread messages
  try {
    const res = await api(`/api/hermes/conversations/${thread.id}/messages`);
    const msgs = res.messages || [];
    const chatMsgContainer = $("chat-messages");
    if (chatMsgContainer) {
      chatMsgContainer.replaceChildren();
      if (msgs.length === 0) {
        addMessage("assistant", `Switched to topic: "${thread.title}". How can I assist you with this strategy?`);
      } else {
        msgs.forEach((m) => {
          addMessage(m.role, m.content, m.role === "assistant" ? "Hermes" : "User");
        });
      }
    }
  } catch (err) {
    notify(`Failed to load messages: ${err.message}`, true);
  }
}

async function createNewConversation() {
  const title = prompt("Enter topic or strategy title:", `Strategy-${new Date().toLocaleDateString("en-GB")}`);
  if (!title) return;
  try {
    const res = await api("/api/hermes/conversations", {
      method: "POST",
      body: { title: title.trim() },
    });
    state.activeConversationId = res.id;
    localStorage.setItem("humming-bird-active-conv-id", res.id);
    setText("active-conv-title", res.title);

    // Switch to Chat tab and clear
    const chatTab = $("tab-hermes-chat");
    if (chatTab) chatTab.click();

    const chatMsgContainer = $("chat-messages");
    if (chatMsgContainer) {
      chatMsgContainer.replaceChildren();
      addMessage("assistant", `Started new conversation topic: "${res.title}". Hermes memory & skills are fully connected.`);
    }
    loadConversations();
  } catch (err) {
    notify(`Failed to create topic: ${err.message}`, true);
  }
}

function formatRelativeTime(isoStr) {
  if (!isoStr) return "";
  try {
    const d = new Date(isoStr);
    const diffSec = Math.floor((Date.now() - d.getTime()) / 1000);
    if (diffSec < 60) return "just now";
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h`;
    return `${Math.floor(diffSec / 86400)}d`;
  } catch {
    return "";
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function executeRollback() {
  if (state.busy) return;
  state.busy = true;
  updateControls();
  try {
    const res = await api("/api/hermes/rollback", { method: "POST" });
    if (res.status === "EMPTY") {
      notify("No previous state checkpoints available to rollback.", true);
    } else {
      notify(`✓ Successfully rolled back: ${res.rolled_back_action || "Last mutation"}`);
      await refresh();
      await loadSystemChanges();
      await loadHermesModels();
    }
  } catch (err) {
    notify(`Rollback failed: ${err.message}`, true);
  } finally {
    state.busy = false;
    updateControls();
  }
}

// --- Hermes AI Brain Model Switcher (3-Tier Fallback) ---
async function loadHermesModels() {
  try {
    const data = await api("/api/hermes/models");
    const active = data.active_model;
    const models = data.models || [];
    const chain = data.fallback_chain || [];

    const shortName = active.split("/").pop();
    setText("hermes-active-model-name", shortName);

    // Sync dropdown menu
    const dropdownList = $("model-dropdown-list");
    if (dropdownList) {
      dropdownList.innerHTML = models.map((m) => {
        const isCur = m.id === active;
        return `
          <button type="button" class="model-opt-btn ${isCur ? "is-active" : ""}" data-model="${m.id}">
            <span>${escapeHtml(m.name)}</span>
            <span class="model-tier-tag">T${m.tier}</span>
          </button>
        `;
      }).join("");

      dropdownList.querySelectorAll(".model-opt-btn").forEach((btn) => {
        btn.addEventListener("click", () => {
          const modId = btn.dataset.model;
          switchHermesModel(modId);
          const drop = $("model-picker-dropdown");
          if (drop) drop.hidden = true;
        });
      });
    }

    // Sync Settings select
    const select = $("settings-model-select");
    if (select) {
      select.value = active;
    }

    // Update settings fallback chain display
    const tier1Label = $("tier1-label");
    if (tier1Label) tier1Label.textContent = active;

    const tier2Badge = $("tier2-badge");
    if (tier2Badge && chain[1]) {
      tier2Badge.textContent = chain[1].status;
      tier2Badge.className = `chain-status-badge ${chain[1].status === "READY" ? "live" : "standby"}`;
    }
  } catch (err) {
    console.warn("Failed to load Hermes models:", err);
  }
}

async function switchHermesModel(modelId) {
  if (!modelId || state.busy) return;
  state.busy = true;
  updateControls();
  try {
    const res = await api("/api/hermes/model", {
      method: "POST",
      body: JSON.stringify({ model: modelId }),
    });
    notify(`🧠 AI Brain switched to ${modelId}`);
    await refresh();
    await loadHermesModels();
    await loadSystemChanges();
  } catch (err) {
    notify(`Failed to switch model: ${err.message}`, true);
  } finally {
    state.busy = false;
    updateControls();
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

  // Model Picker Dropdown toggle (Bottom model button above chat input)
  const modelBtn = $("hermes-bottom-model-btn") || $("hermes-model-btn");
  const modelDrop = $("model-picker-dropdown");
  if (modelBtn && modelDrop) {
    modelBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      modelDrop.hidden = !modelDrop.hidden;
    });
    document.addEventListener("click", (e) => {
      if (!modelDrop.contains(e.target) && e.target !== modelBtn) {
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

// --- API Keys, Quotas & Telemetry Settings ---
async function loadApiKeysSettings() {
  try {
    const data = await api("/api/settings/keys");
    const hasOr = Boolean(data.openrouter_configured || data.has_openrouter_key || data.openrouter_key_masked);
    const hasGemini = Boolean(data.gemini_configured || data.has_gemini_key || data.gemini_key_masked);
    const hintOr = $("hint-openrouter");
    if (hintOr) hintOr.textContent = hasOr ? "Configured: Yes (Masked)" : "Configured: No (Falling back to Gemini/Local)";
    const hintGemini = $("hint-gemini");
    if (hintGemini) hintGemini.textContent = hasGemini ? "Configured: Yes (Masked)" : "Configured: No (Optional fallback)";

    const orInput = $("key-openrouter");
    if (orInput && hasOr && !orInput.value) {
      orInput.placeholder = data.openrouter_key_masked || "sk-or-v1-••••••••";
    }
    const geminiInput = $("key-gemini");
    if (geminiInput && hasGemini && !geminiInput.value) {
      geminiInput.placeholder = data.gemini_key_masked || "AIzaSy••••••••";
    }
    const tgToken = $("key-telegram-token");
    if (tgToken && data.telegram_bot_token_masked && !tgToken.value) {
      tgToken.placeholder = data.telegram_bot_token_masked;
    }
    const tgChat = $("key-telegram-chat");
    if (tgChat && (data.telegram_chat_id || data.telegram_chat_id_masked) && !tgChat.value) {
      tgChat.value = data.telegram_chat_id || data.telegram_chat_id_masked || "";
    }
    const limitInput = $("key-daily-limit");
    if (limitInput) limitInput.value = data.daily_call_limit || 30;

    // Telemetry quota bar
    const callsUsed = data.daily_calls_used !== undefined ? data.daily_calls_used : (data.calls_used_today || 0);
    const limit = data.daily_call_limit || 30;
    const pct = Math.min(100, Math.round((callsUsed / limit) * 100));
    setText("telemetry-usage-text", `${callsUsed} / ${limit} calls used`);
    const quotaBar = $("telemetry-quota-bar");
    if (quotaBar) quotaBar.style.width = `${pct}%`;
  } catch (err) {
    console.warn("Could not load API keys settings:", err);
  }
}

async function saveApiKeysSettings(e) {
  if (e) e.preventDefault();
  const orKey = $("key-openrouter")?.value?.trim();
  const geminiKey = $("key-gemini")?.value?.trim();
  const tgToken = $("key-telegram-token")?.value?.trim();
  const tgChat = $("key-telegram-chat")?.value?.trim();
  const limit = parseInt($("key-daily-limit")?.value || "30", 10);

  const payload = { daily_call_limit: limit };
  if (orKey) payload.openrouter_key = orKey;
  if (geminiKey) payload.gemini_key = geminiKey;
  if (tgToken) payload.telegram_bot_token = tgToken;
  if (tgChat) payload.telegram_chat_id = tgChat;

  const statusMsg = $("keys-save-status");
  try {
    await api("/api/settings/keys", {
      method: "POST",
      body: payload,
    });
    if (statusMsg) {
      statusMsg.textContent = "✓ Settings saved securely";
      statusMsg.className = "save-status-msg success";
      setTimeout(() => { if (statusMsg) statusMsg.textContent = ""; }, 3000);
    }
    notify("API Keys & Quotas updated successfully");
    if (orKey && $("key-openrouter")) $("key-openrouter").value = "";
    if (geminiKey && $("key-gemini")) $("key-gemini").value = "";
    if (tgToken && $("key-telegram-token")) $("key-telegram-token").value = "";
    loadApiKeysSettings();
  } catch (err) {
    if (statusMsg) {
      statusMsg.textContent = `! ${err.message}`;
      statusMsg.className = "save-status-msg error";
    }
    showError(err.message);
  }
}

// --- Operator Profile & Login Gate Authentication ---
async function checkAuthSession() {
  try {
    const res = await api("/api/auth/session");
    if (res && res.authenticated) {
      const loginGate = $("login-gate-overlay");
      if (loginGate && loginGate.open) loginGate.close();
      const user = res.user || {};
      setText("op-name", user.name || res.operator_name || "Hasibur Rahman");
      setText("op-username", user.username || res.operator_username || "01882082502");
      setText("op-portfolio", user.portfolio || res.linked_portfolio || "Humming Bird (StockNow)");
      return true;
    }
  } catch (err) {
    console.warn("Auth session check:", err);
  }
  return false;
}

function openOperatorProfile() {
  const modal = $("operator-modal");
  if (modal) modal.showModal();
}

function closeOperatorProfile() {
  const modal = $("operator-modal");
  if (modal) modal.close();
}

async function handleOperatorLogin(e) {
  if (e) e.preventDefault();
  const username = $("login-username")?.value?.trim();
  const password = $("login-password")?.value?.trim();
  const errEl = $("login-error-msg");
  if (errEl) errEl.hidden = true;

  try {
    const res = await api("/api/auth/login", {
      method: "POST",
      body: { username, password },
    });
    if (res && (res.status === "ok" || res.authenticated)) {
      const loginGate = $("login-gate-overlay");
      if (loginGate) loginGate.close();
      const user = res.user || {};
      const opName = user.name || res.operator_name || "Hasibur Rahman";
      notify(`Welcome back, ${opName}!`);
      checkAuthSession();
      refresh();
    }
  } catch (err) {
    if (errEl) {
      errEl.textContent = err.message || "Invalid credentials";
      errEl.hidden = false;
    }
  }
}

async function handleOperatorLogout() {
  try {
    await api("/api/auth/logout", { method: "POST" });
  } catch (e) {}
  closeOperatorProfile();
  const loginGate = $("login-gate-overlay");
  if (loginGate) loginGate.showModal();
  notify("Cockpit session locked");
}

function initAuthAndSettings() {
  // Bind API keys form
  const keysForm = $("api-keys-form");
  if (keysForm) keysForm.addEventListener("submit", saveApiKeysSettings);

  // Key visibility toggles
  document.querySelectorAll(".key-toggle-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      const inp = $(targetId);
      if (inp) {
        inp.type = inp.type === "password" ? "text" : "password";
      }
    });
  });

  // Bind operator avatar & profile modal
  const avatarBtn = $("user-avatar-btn");
  if (avatarBtn) avatarBtn.addEventListener("click", openOperatorProfile);

  const opCloseBtn = $("op-close-btn");
  if (opCloseBtn) opCloseBtn.addEventListener("click", closeOperatorProfile);

  const opBackdrop = $("op-backdrop");
  if (opBackdrop) opBackdrop.addEventListener("click", closeOperatorProfile);

  const lockBtn = $("lock-cockpit-btn");
  if (lockBtn) lockBtn.addEventListener("click", handleOperatorLogout);

  // Bind Login form & 1-click autofill
  const loginForm = $("login-form");
  if (loginForm) loginForm.addEventListener("submit", handleOperatorLogin);

  const autofillBtn = $("login-autofill-btn");
  if (autofillBtn) {
    autofillBtn.addEventListener("click", () => {
      const u = $("login-username");
      const p = $("login-password");
      if (u) u.value = "01882082502";
      if (p) p.value = "Stocknow#909109";
      handleOperatorLogin();
    });
  }

  // Check initial session
  checkAuthSession();
}

// --- Files Changed & System Audit Diffs ---
async function loadSystemChanges() {
  const fileContainer = $("files-changed-list");
  const diffContainer = $("changes-diff-list");
  const cpContainer = $("changes-checkpoints-list");
  try {
    const res = await api("/api/system/changes");
    const changes = res.changes || [];
    const files = res.files_changed || [];
    const checkpoints = res.checkpoints || [];

    const totalCount = Math.max(changes.length, files.length);
    setText("changes-badge", totalCount);
    setText("changes-badge-count", changes.length);
    setText("files-changed-count-tag", files.length);

    // Render structured audit diffs
    if (diffContainer) {
      if (changes.length === 0) {
        diffContainer.replaceChildren(element("div", "empty-state-small", "No recent system or rule changes recorded. Checkpoints are logged automatically on every mutation."));
      } else {
        diffContainer.innerHTML = changes.map((c) => {
          const diff = c.diff || {};
          const diffLines = diff.diff_lines || [];
          const linesHtml = diffLines.map((l) => `<div class="diff-line ${l.type === "del" ? "diff-del" : "diff-add"}">${escapeHtml(l.text)}</div>`).join("");
          return `
            <article class="diff-card">
              <div class="diff-card-head">
                <div class="diff-head-meta">
                  <span class="diff-action-tag">${escapeHtml(c.action || "MUTATION")}</span>
                  <span class="diff-actor-tag">${escapeHtml(c.actor || "Hermes Agent")}</span>
                  <span class="diff-time">${escapeHtml(formatRelativeTime(c.created_at) || c.date || "")}</span>
                </div>
                <button type="button" class="diff-revert-btn" onclick="executeRollback()" title="Undo mutation (/rollback)">↺ Rollback</button>
              </div>
              <div class="diff-card-body">
                <div class="diff-summary-text">${escapeHtml(c.description || diff.summary || "")}</div>
                <div class="diff-lines-wrap">${linesHtml || `<div class="diff-line diff-add">+ ${escapeHtml(c.description)}</div>`}</div>
              </div>
            </article>
          `;
        }).join("");
      }
    }

    if (fileContainer) {
      if (files.length === 0) {
        fileContainer.replaceChildren(element("div", "empty-state-small", "Workspace working tree is clean."));
      } else {
        const items = files.map((f) => {
          const item = element("div", "file-change-item");
          const chip = element("span", `file-status-chip status-${f.status}`, f.status);
          const info = element("div", "file-info");
          info.append(
            element("span", "file-name", f.name),
            element("span", "file-folder", f.folder)
          );
          item.append(chip, info);
          return item;
        });
        fileContainer.replaceChildren(...items);
      }
    }

    if (cpContainer) {
      if (checkpoints.length === 0) {
        cpContainer.replaceChildren(element("div", "empty-state-small", "No recent state checkpoints."));
      } else {
        const cpItems = checkpoints.map((cp) => {
          const item = element("div", "cp-item");
          const head = element("div", "cp-head");
          head.append(
            element("strong", "", cp.action.replaceAll("_", " ")),
            element("span", "conv-time", formatRelativeTime(cp.created_at))
          );
          const desc = element("div", "cp-desc", cp.description);
          item.append(head, desc);
          return item;
        });
        cpContainer.replaceChildren(...cpItems);
      }
    }
  } catch (err) {
    if (diffContainer) diffContainer.replaceChildren(element("div", "empty-state-small", `Failed to load changes: ${err.message}`));
    if (fileContainer) fileContainer.replaceChildren(element("div", "empty-state-small", `Failed to load changes: ${err.message}`));
  }
}

updateControls();
refresh();
initRealtimeStream();
initHermesSidebar();
loadConversations();
loadHermesModels();
loadSystemChanges();
initAuthAndSettings();
initViewRouter();
