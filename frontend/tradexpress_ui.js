/**
 * TradeXpress 2.0 3-Pane Cockpit UI Controller
 * Manages Market Watch interactions, 2-step limit order execution, 5-level market depth,
 * monitor panels (Order List, Portfolio, Account Summary, Order Search), learning views,
 * and passive feed guidance.
 */

(function () {
  "use strict";

  const state = {
    selectedSymbol: "BANKASIA",
    selectedSide: "BUY",
    qty: 10,
    price: 18.40,
    activeNavView: "trade",
    activeMonPane: "order-list",
    pendingPreview: null,
    orders: [],
    learningSummary: null,
    feedStatus: null,
  };

  function toTradeXpressSymbol(sym) {
    if (!sym) return "";
    const clean = sym.replace(/[`'][A-Za-z0-9_]+$/, "").trim().toUpperCase();
    return `${clean}\`PB`;
  }

  function cleanSymbol(raw) {
    if (!raw) return "";
    return raw.replace(/[`'][A-Za-z0-9_]+$/, "").trim().toUpperCase();
  }

  function calcBrokerFee(gross) {
    const commission = gross * 0.004;
    const vat = commission * 0.15;
    return Math.round((commission + vat) * 100) / 100;
  }

  function formatMoney(val) {
    const n = Number(val) || 0;
    return "৳" + n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }

  function formatPct(val) {
    const n = Number(val) || 0;
    const sign = n >= 0 ? "+" : "";
    return `${sign}${n.toFixed(2)}%`;
  }

  // --- 1. Secondary Navigation Switching ---
  function switchNavView(viewName) {
    state.activeNavView = viewName;
    document.querySelectorAll(".tx-nav-tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.txView === viewName);
    });

    const views = {
      trade: document.getElementById("view-dashboard") || document.getElementById("tx-trade-workspace"),
      heatmap: document.getElementById("view-heatmap-wrap"),
      rules: document.getElementById("view-rules-wrap"),
      ledger: document.getElementById("view-ledger-wrap"),
      learning: document.getElementById("tx-learning-view"),
      settings: document.getElementById("view-settings"),
    };

    Object.entries(views).forEach(([k, el]) => {
      if (!el) return;
      if (k === viewName) {
        el.classList.remove("view-hidden");
        el.classList.add("active");
        el.hidden = false;
      } else {
        el.classList.add("view-hidden");
        el.classList.remove("active");
        el.hidden = true;
      }
    });

    if (viewName === "learning") {
      loadLearningSummary();
    } else if (viewName === "settings") {
      loadFeedStatus();
    } else if (viewName === "heatmap" && typeof window.renderMarketMap === "function") {
      setTimeout(() => {
        window.renderMarketMap();
        if (typeof window.renderTopSectorsChart === "function") {
          window.renderTopSectorsChart();
        }
      }, 50);
    }
  }

  // --- 2. Monitor Panel Switching ---
  function switchMonPane(paneName) {
    state.activeMonPane = paneName;
    document.querySelectorAll(".tx-mon-tab").forEach((tab) => {
      tab.classList.toggle("active", tab.dataset.monPane === paneName);
    });

    const panes = {
      "order-list": document.getElementById("tx-pane-order-list"),
      portfolio: document.getElementById("tx-pane-portfolio"),
      "account-summary": document.getElementById("tx-pane-account-summary"),
      "order-search": document.getElementById("tx-pane-order-search"),
    };

    Object.entries(panes).forEach(([k, el]) => {
      if (!el) return;
      el.hidden = k !== paneName;
    });

    if (paneName === "order-list") {
      loadOrders();
    }
  }

  // --- 3. Order Ticket Calculation & Update ---
  function updateOrderTicketCalculations() {
    const qtyInput = document.getElementById("tx-order-qty");
    const priceInput = document.getElementById("tx-order-price");
    const submitBtn = document.getElementById("tx-order-submit-btn");

    const qty = parseInt(qtyInput ? qtyInput.value : "10", 10) || 1;
    const price = parseFloat(priceInput ? priceInput.value : "18.40") || 0;
    state.qty = qty;
    state.price = price;

    const gross = qty * price;
    const fee = calcBrokerFee(gross);
    const net = state.selectedSide === "BUY" ? gross + fee : Math.max(0, gross - fee);

    const valEl = document.getElementById("tx-ticket-order-val");
    const feeEl = document.getElementById("tx-ticket-fee");
    const netEl = document.getElementById("tx-ticket-net-val");

    if (valEl) valEl.textContent = formatMoney(gross);
    if (feeEl) feeEl.textContent = formatMoney(fee);
    if (netEl) netEl.textContent = formatMoney(net);

    if (submitBtn) {
      submitBtn.textContent = `${state.selectedSide === "BUY" ? "Buy" : "Sell"} @ ${price.toFixed(2)}`;
      submitBtn.className = `button primary ${state.selectedSide === "BUY" ? "tx-submit-buy" : "tx-submit-sell"}`;
    }
  }

  function selectSymbolForTicket(symbol) {
    const sym = cleanSymbol(symbol);
    state.selectedSymbol = sym;

    let company = null;
    const comps = state.lastSnapshot?.companies || window.state?.snapshot?.companies || [];
    if (comps && comps.length > 0) {
      company = comps.find((c) => c.symbol === sym);
    }

    const txSym = toTradeXpressSymbol(sym);

    // Update Header
    const hdrTitle = document.getElementById("tx-ticket-header-title");
    if (hdrTitle) hdrTitle.textContent = `New Order - ${txSym} (DSE · SHADOW)`;

    // Update Symbol Info Strip
    const catEl = document.getElementById("tx-ticket-cat");
    const symEl = document.getElementById("tx-ticket-sym");
    const ltpEl = document.getElementById("tx-ticket-ltp");
    const chgEl = document.getElementById("tx-ticket-chgpct");
    const minmaxEl = document.getElementById("tx-ticket-minmax");
    const bidofferEl = document.getElementById("tx-ticket-bidoffer");
    const lowhighEl = document.getElementById("tx-ticket-lowhigh");
    const availQtyEl = document.getElementById("tx-ticket-avail-qty");
    const gainlossEl = document.getElementById("tx-ticket-gainloss");

    if (catEl) catEl.textContent = (company && company.symbol_category) || "A";
    if (symEl) symEl.textContent = txSym;

    const ltp = (company && (company.last_price ?? company.price)) || 17.50;
    const chgPct = (company && company.curve && company.curve.day_change_pct) || 0;
    if (ltpEl) ltpEl.textContent = Number(ltp).toFixed(2);
    if (chgEl) {
      chgEl.textContent = formatPct(chgPct);
      chgEl.className = chgPct >= 0 ? "positive" : "negative";
    }

    const minLimit = (company && company.min_limit) || (ltp * 0.9).toFixed(2);
    const maxLimit = (company && company.max_limit) || (ltp * 1.1).toFixed(2);
    if (minmaxEl) minmaxEl.textContent = `${Number(minLimit).toFixed(2)} / ${Number(maxLimit).toFixed(2)}`;

    const bid = (company && company.bid) || (ltp - 0.10);
    const offer = (company && company.offer) || ltp;
    if (bidofferEl) {
      bidofferEl.innerHTML = `<span class="positive">${Number(bid).toFixed(2)}</span> / <span class="negative">${Number(offer).toFixed(2)}</span>`;
    }

    const low = (company && company.curve && company.curve.low) || ltp;
    const high = (company && company.curve && company.curve.high) || ltp;
    if (lowhighEl) lowhighEl.textContent = `${Number(low).toFixed(2)} / ${Number(high).toFixed(2)}`;

    // Available Saleable Qty (matured T+2 shares)
    const matureQty = (company && (company.mature_shares ?? company.mature_qty)) || 0;
    if (availQtyEl) availQtyEl.textContent = String(matureQty);

    // Gain/Loss pill
    if (gainlossEl) {
      const netProfit = (company && company.net_profit_bdt) || 0;
      const profitPct = (company && company.net_profit_pct) || 0;
      gainlossEl.textContent = `${netProfit >= 0 ? "+" : ""}${netProfit.toFixed(2)} (${formatPct(profitPct)})`;
      gainlossEl.className = `tx-gainloss-pill ${netProfit >= 0 ? "positive" : "negative"}`;
    }

    // Default Price
    const priceInput = document.getElementById("tx-order-price");
    if (priceInput) {
      const targetP = state.selectedSide === "BUY" ? (offer > 0 ? offer : ltp) : (bid > 0 ? bid : ltp);
      priceInput.value = Number(targetP).toFixed(2);
    }

    renderMarketDepthTable(bid, offer, company ? company.order_book_depth : null, company);
    updateOrderTicketCalculations();
  }

  function setOrderSide(side) {
    state.selectedSide = side;
    const buyBtn = document.getElementById("tx-side-buy-btn");
    const sellBtn = document.getElementById("tx-side-sell-btn");

    if (buyBtn) buyBtn.classList.toggle("active", side === "BUY");
    if (sellBtn) sellBtn.classList.toggle("active", side === "SELL");

    // Adjust price to best bid/offer for selected symbol
    selectSymbolForTicket(state.selectedSymbol);
  }

  function quickSell(symbol, matureQty, ltp) {
    setOrderSide("SELL");
    selectSymbolForTicket(symbol);
    const qtyInput = document.getElementById("tx-order-qty");
    if (qtyInput) {
      qtyInput.value = matureQty > 0 ? matureQty : 1;
    }
    updateOrderTicketCalculations();

    const ticketEl = document.getElementById("tx-order-ticket");
    if (ticketEl) {
      ticketEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }

  // --- 4. 5-Level Market Depth Table ---
  function renderMarketDepthTable(baseBid, baseOffer, customDepth, company) {
    const tableBody = document.getElementById("tx-depth-body");
    if (!tableBody) return;

    // Check if real 5-level depth captured from TradeXpress Order Ticket
    if (customDepth && Array.isArray(customDepth.levels) && customDepth.levels.length > 0) {
      let rowsHtml = "";
      customDepth.levels.forEach((lvl) => {
        const bQty = Number(lvl.bid_qty || 0);
        const bP = Number(lvl.bid_price || 0).toFixed(2);
        const oP = Number(lvl.offer_price || 0).toFixed(2);
        const oQty = Number(lvl.offer_qty || 0);
        rowsHtml += `
          <tr>
            <td class="align-right tx-depth-qty">${bQty > 0 ? bQty.toLocaleString() : "—"}</td>
            <td class="align-right tx-depth-bid" data-price="${bP}" title="Click to fill price">${bP !== "0.00" ? bP : "—"}</td>
            <td class="align-right tx-depth-offer" data-price="${oP}" title="Click to fill price">${oP !== "0.00" ? oP : "—"}</td>
            <td class="align-right tx-depth-qty">${oQty > 0 ? oQty.toLocaleString() : "—"}</td>
          </tr>
        `;
      });
      tableBody.innerHTML = rowsHtml;
      _attachDepthClickToFill(tableBody);
      return;
    }

    // Single L1 BBO (No fake generated quantities)
    const b = Number(baseBid) || 0;
    const o = Number(baseOffer) || 0;
    const bQty = (company && company.bid_qty) ? Number(company.bid_qty).toLocaleString() : "—";
    const oQty = (company && company.offer_qty) ? Number(company.offer_qty).toLocaleString() : "—";
    const sym = (company && company.symbol) || state.selectedSymbol || "symbol";

    if (b > 0 || o > 0) {
      const bStr = b > 0 ? b.toFixed(2) : "—";
      const oStr = o > 0 ? o.toFixed(2) : "—";
      tableBody.innerHTML = `
        <tr>
          <td class="align-right tx-depth-qty">${bQty}</td>
          <td class="align-right tx-depth-bid" data-price="${b > 0 ? b.toFixed(2) : ''}" title="Click to fill price">${bStr}</td>
          <td class="align-right tx-depth-offer" data-price="${o > 0 ? o.toFixed(2) : ''}" title="Click to fill price">${oStr}</td>
          <td class="align-right tx-depth-qty">${oQty}</td>
        </tr>
        <tr>
          <td colspan="4" class="align-center muted small" style="padding: 6px 4px; font-size: 10px;">
            Live L1 BBO · Select ${sym} in TradeXpress for 5-level depth
          </td>
        </tr>
      `;
      _attachDepthClickToFill(tableBody);
      return;
    }

    // Off-hours / SOD
    tableBody.innerHTML = `
      <tr>
        <td colspan="4" class="align-center muted small" style="padding: 12px 4px; font-size: 10.5px;">
          Market depth waiting for session open / quotes…
        </td>
      </tr>
    `;
  }

  function _attachDepthClickToFill(tableBody) {
    tableBody.querySelectorAll("td[data-price]").forEach((td) => {
      td.addEventListener("click", () => {
        const p = parseFloat(td.dataset.price);
        const priceInput = document.getElementById("tx-order-price");
        if (priceInput && p > 0) {
          priceInput.value = p.toFixed(2);
          updateOrderTicketCalculations();
        }
      });
    });
  }

  // --- 5. 2-Step Limit Execution Lifecycle ---
  async function submitOrderPreview() {
    const sym = state.selectedSymbol;
    const side = state.selectedSide;
    const qty = state.qty;
    const price = state.price;

    if (!sym || qty <= 0 || price <= 0) {
      alert("Please enter a valid symbol, quantity, and limit price.");
      return;
    }

    try {
      const res = await fetch("/api/tradexpress/shadow-order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: sym,
          side: side,
          quantity: qty,
          price: price,
          confirm: false,
          portfolio_id: "H9210_SHADOW",
        }),
      });

      const data = await res.json();
      if (!res.ok || data.status === "REJECTED") {
        const errorMsg = (data.errors && data.errors.join("; ")) || data.message || "Order rejected by preflight.";
        showToast(`Order Rejected: ${errorMsg}`, true);
        return;
      }

      state.pendingPreview = data;
      openConfirmModal(data);
    } catch (err) {
      showToast(`Network error: ${err.message}`, true);
    }
  }

  function openConfirmModal(data) {
    const modal = document.getElementById("tx-confirm-order-modal");
    if (!modal) return;

    const isBuy = data.side === "BUY";
    const banner = document.getElementById("tx-confirm-banner");
    const bannerTitle = document.getElementById("tx-confirm-banner-title");
    const subtitle = document.getElementById("tx-confirm-subtitle");
    const submitBtn = document.getElementById("tx-confirm-submit-btn");

    if (banner) {
      banner.className = `tx-confirm-banner ${isBuy ? "tx-confirm-banner-buy" : "tx-confirm-banner-sell"}`;
    }
    if (bannerTitle) {
      bannerTitle.textContent = `Confirm Order  ${data.tradexpress_symbol || toTradeXpressSymbol(data.symbol)}`;
    }
    if (subtitle) {
      subtitle.textContent = `${data.symbol} | DSE | Main (SHADOW DUMMY — 0 BDT RISK)`;
    }

    // Grid fields
    setText("tx-confirm-side", data.side);
    setText("tx-confirm-price", Number(data.limit_price).toFixed(2));
    setText("tx-confirm-qty", String(data.quantity));
    setText("tx-confirm-fee", formatMoney(data.estimated_fee));
    setText("tx-confirm-order-val", formatMoney(data.order_value));
    setText("tx-confirm-net-val", formatMoney(data.net_value));

    if (submitBtn) {
      submitBtn.className = `button primary ${isBuy ? "tx-btn-confirm-buy" : "tx-btn-confirm-sell"}`;
      submitBtn.textContent = `Confirm ${data.side} Order`;
    }

    modal.showModal();
  }

  async function executeConfirmedOrder() {
    const preview = state.pendingPreview;
    if (!preview) return;

    const modal = document.getElementById("tx-confirm-order-modal");
    try {
      const res = await fetch("/api/tradexpress/shadow-order", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          symbol: preview.symbol,
          side: preview.side,
          quantity: preview.quantity,
          price: preview.limit_price,
          confirm: true,
          portfolio_id: "H9210_SHADOW",
        }),
      });

      const data = await res.json();
      if (modal) modal.close();

      if (!res.ok || data.status === "REJECTED") {
        const errorMsg = (data.errors && data.errors.join("; ")) || data.message || "Execution failed.";
        showToast(`Execution Failed: ${errorMsg}`, true);
        return;
      }

      const txSym = preview.tradexpress_symbol || toTradeXpressSymbol(preview.symbol);
      const toastText = `${preview.side} ${txSym} : ${preview.quantity} @ ${Number(preview.limit_price).toFixed(2)} : ${data.status}`;
      showToast(toastText, false);

      // Refresh monitor panels and snapshot
      loadOrders();
      loadLearningSummary();
      if (typeof window.refresh === "function") {
        window.refresh(true);
      }
    } catch (err) {
      if (modal) modal.close();
      showToast(`Execution error: ${err.message}`, true);
    }
  }

  // --- 6. Order List & Cancellation ---
  async function loadOrders() {
    try {
      const res = await fetch("/api/tradexpress/orders?portfolio_id=H9210_SHADOW&limit=50");
      if (!res.ok) return;
      const orders = await res.json();
      state.orders = orders;
      renderOrdersTable(orders);
    } catch (err) {
      console.warn("Failed loading orders:", err);
    }
  }

  function renderOrdersTable(orders) {
    const tbody = document.getElementById("tx-orders-body");
    const countEl = document.getElementById("tx-order-count");
    if (countEl) countEl.textContent = String(orders.length);
    if (!tbody) return;

    if (!orders.length) {
      tbody.innerHTML = `<tr><td colspan="11" class="loading-cell">No shadow orders placed yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = orders
      .map((o) => {
        const statusClass = `tx-status-${o.status.toLowerCase()}`;
        const cancelBtn =
          o.status === "QUEUED"
            ? `<button type="button" class="tx-cancel-order-btn" data-ref="${o.order_ref}" title="Cancel resting order">Cancel</button>`
            : `<span class="muted">—</span>`;

        return `
          <tr>
            <td><strong>${toTradeXpressSymbol(o.symbol)}</strong></td>
            <td class="small muted">${o.order_ref}</td>
            <td>H9210</td>
            <td><span class="tx-badge-status ${statusClass}">${o.status}</span></td>
            <td><span class="${o.side === "BUY" ? "positive" : "negative"}">${o.side}</span></td>
            <td class="align-right">${o.quantity}</td>
            <td class="align-right">৳${Number(o.limit_price).toFixed(2)}</td>
            <td class="align-right">${o.filled_qty}</td>
            <td class="align-right">${o.pending_qty}</td>
            <td class="align-right">৳${Number(o.order_value).toFixed(2)}</td>
            <td class="align-center">${cancelBtn}</td>
          </tr>
        `;
      })
      .join("");

    tbody.querySelectorAll(".tx-cancel-order-btn").forEach((btn) => {
      btn.addEventListener("click", () => cancelOrder(btn.dataset.ref));
    });
  }

  async function cancelOrder(orderRef) {
    try {
      const res = await fetch(`/api/tradexpress/shadow-order/${orderRef}/cancel`, { method: "POST" });
      const data = await res.json();
      if (!res.ok || data.status === "ERROR") {
        showToast(data.message || "Failed to cancel order.", true);
        return;
      }
      showToast(`Order ${orderRef} cancelled.`, false);
      loadOrders();
      if (typeof window.refresh === "function") {
        window.refresh(true);
      }
    } catch (err) {
      showToast(`Cancel error: ${err.message}`, true);
    }
  }

  // --- 7. Learning Summary View ---
  async function loadLearningSummary() {
    try {
      const res = await fetch("/api/tradexpress/learning?limit=50");
      if (!res.ok) return;
      const data = await res.json();
      state.learningSummary = data;
      renderLearningView(data);
    } catch (err) {
      console.warn("Failed loading learning summary:", err);
    }
  }

  function renderLearningView(data) {
    setText("tx-learn-total", String(data.total_records));
    setText("tx-learn-win-rate", `${data.win_rate_pct.toFixed(1)}%`);
    setText("tx-learn-buys", String(data.buys_count));
    setText("tx-learn-sells", String(data.sells_count));
    setText("tx-learn-avg-pnl", formatPct(data.avg_net_pnl_pct));

    const tbody = document.getElementById("tx-learn-body");
    if (!tbody) return;

    if (!data.recent_logs || !data.recent_logs.length) {
      tbody.innerHTML = `<tr><td colspan="10" class="loading-cell">No trade learning records logged yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.recent_logs
      .map((l) => {
        const pnlStr = l.net_pnl_pct !== null ? formatPct(l.net_pnl_pct) : "—";
        const pnlClass = l.net_pnl_pct !== null && l.net_pnl_pct >= 0 ? "positive" : "negative";
        return `
          <tr>
            <td class="small muted">${l.session_on || "—"}</td>
            <td><strong>${toTradeXpressSymbol(l.symbol)}</strong></td>
            <td><span class="cat-tag cat-${(l.tier || "GSC").toLowerCase()}">${l.tier}</span></td>
            <td><span class="${l.side === "BUY" ? "positive" : "negative"}">${l.side}</span></td>
            <td><span class="tx-badge-outcome">${l.outcome_type}</span></td>
            <td class="align-right">৳${Number(l.entry_price).toFixed(2)}</td>
            <td class="align-right">${l.exit_price ? "৳" + Number(l.exit_price).toFixed(2) : "—"}</td>
            <td class="align-right ${pnlClass}">${pnlStr}</td>
            <td class="small">${l.actor}</td>
            <td class="small muted">${l.lesson_summary}</td>
          </tr>
        `;
      })
      .join("");
  }

  // --- 8. Passive Feed Status & Guidance ---
  async function loadFeedStatus() {
    try {
      const res = await fetch("/api/tradexpress/status");
      if (!res.ok) return;
      const data = await res.json();
      state.feedStatus = data;
      renderFeedStatusCard(data);
    } catch (err) {
      console.warn("Failed loading feed status:", err);
    }
  }

  async function controlBridge(action) {
    const spyBtn = document.getElementById("tx-passive-spy-btn");
    try {
      if (spyBtn) spyBtn.disabled = true;
      const resp = await fetch("/api/tradexpress/bridge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action, cdp_url: "http://127.0.0.1:9222" }),
      });
      const data = await resp.json();
      showToast(action === "attach" ? "Connecting to Chrome CDP Spy (port 9222)..." : "CDP Spy detached.");
      await loadFeedStatus();
    } catch (err) {
      showToast(`Bridge error: ${err.message}`, true);
    } finally {
      if (spyBtn) spyBtn.disabled = false;
    }
  }

  function renderFeedStatusCard(data) {
    const cdpBadge = document.getElementById("tx-feed-cdp-badge");
    const healthBadge = document.getElementById("tx-feed-health-badge");
    const guidanceList = document.getElementById("tx-feed-guidance-list");
    const tabsStatus = document.getElementById("tx-feed-tabs-status");
    const spyBtn = document.getElementById("tx-passive-spy-btn");
    const bridgeStats = document.getElementById("tx-feed-bridge-stats");

    const daemon = data.daemon || {};
    const isSpyLive = daemon.running && daemon.cdp_connected;
    const isExtLive = data.bridge_connected && data.bridge_source === "EDGE_EXTENSION_PASSIVE";

    if (spyBtn) {
      if (isExtLive) {
        spyBtn.textContent = `🟢 Passive Mirror: LIVE (Edge Ext · ${data.active_tab || "MW"})`;
        spyBtn.classList.add("active");
        spyBtn.title = `Edge Extension Passive Mirror active (${data.active_tab || "market_watch"}). Click to toggle CDP fallback.`;
      } else if (isSpyLive) {
        spyBtn.textContent = "📡 Passive Spy: LIVE";
        spyBtn.classList.add("active");
        spyBtn.title = `CDP Connected (${daemon.active_tab || "TradeXpress"}). Click to detach.`;
      } else if (daemon.running) {
        spyBtn.textContent = "📡 Passive Spy: CONNECTING";
        spyBtn.classList.remove("active");
        spyBtn.title = "Attempting to connect to CDP port 9222... Click to detach.";
      } else {
        spyBtn.textContent = "📡 Passive Spy: OFF";
        spyBtn.classList.remove("active");
        spyBtn.title = "Click to attach read-only passive CDP spy (port 9222)";
      }
    }

    if (cdpBadge) {
      if (isExtLive) {
        cdpBadge.textContent = `MIRROR: LIVE (Edge Ext · ${data.active_tab || "MW"})`;
        cdpBadge.className = "sys-badge teal-badge";
      } else if (data.cdp_connected || isSpyLive) {
        cdpBadge.textContent = "CDP: ONLINE";
        cdpBadge.className = "sys-badge teal-badge";
      } else {
        cdpBadge.textContent = "FEED: OFFLINE";
        cdpBadge.className = "sys-badge amber-badge";
      }
    }

    if (healthBadge) {
      const isHealthy = data.guidance && data.guidance.is_healthy;
      healthBadge.textContent = isHealthy ? "FEED HEALTHY" : "ATTENTION REQUIRED";
      healthBadge.className = `sys-badge ${isHealthy ? "teal-badge" : "red-badge"}`;
    }

    if (bridgeStats) {
      bridgeStats.innerHTML = `
        <div class="tx-tab-status-row"><span>Active Source</span><span>${isExtLive ? '<span class="positive">● EDGE EXTENSION PASSIVE</span>' : (isSpyLive ? '<span class="positive">● CDP SPY (PORT 9222)</span>' : '<span class="muted">OFFLINE</span>')}</span></div>
        <div class="tx-tab-status-row"><span>Active Tab</span><span>${data.active_tab || daemon.active_tab || '<span class="muted">None</span>'}</span></div>
        <div class="tx-tab-status-row"><span>DSE Status</span><span><strong>${data.dse_status || "UNKNOWN"}</strong></span></div>
        <div class="tx-tab-status-row"><span>Telemetry Ingested</span><span><small>${data.total_ingests_count || 0} Ingests · ${daemon.dom_syncs_count || 0} DOM · ${daemon.ws_frames_count || 0} WS</small></span></div>
        ${daemon.last_error ? `<div class="tx-tab-status-row negative"><small>${daemon.last_error}</small></div>` : ""}
      `;
    }

    if (tabsStatus && data.guidance && data.guidance.freshness) {
      const f = data.guidance.freshness;
      tabsStatus.innerHTML = Object.entries(f)
        .map(([k, item]) => {
          const freshTag = item.is_fresh ? `<span class="positive">● Fresh</span>` : `<span class="negative">○ Stale</span>`;
          const ageStr = item.age_seconds !== null ? `(${Math.round(item.age_seconds)}s ago)` : "(No ticks)";
          return `<div class="tx-tab-status-row"><span>${item.label}</span><span>${freshTag} <small class="muted">${ageStr}</small></span></div>`;
        })
        .join("");
    }

    if (guidanceList && data.guidance && data.guidance.operator_instructions) {
      guidanceList.innerHTML = data.guidance.operator_instructions
        .map((i) => `<li>${i}</li>`)
        .join("");
    }
  }

  // --- 9. Donut Chart for Account Summary ---
  function renderAccountDonut(settled, unsettled, invested) {
    const container = document.getElementById("tx-account-donut");
    if (!container) return;

    const total = settled + unsettled + invested;
    if (total <= 0) {
      container.innerHTML = `<span class="muted small">No asset data</span>`;
      return;
    }

    const r = 36;
    const c = 50;
    const circ = 2 * Math.PI * r;

    // Crisp 100% Cash Donut when invested == 0
    if (invested <= 0) {
      container.innerHTML = `
        <svg viewBox="0 0 100 100" class="tx-donut-svg">
          <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="var(--tx-border, #1c2837)" stroke-width="12" />
          <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#22c55e" stroke-width="12"
            stroke-dasharray="${circ} 0" stroke-dashoffset="0" />
          <text x="${c}" y="${c - 2}" text-anchor="middle" font-size="9" font-weight="700" fill="#22c55e">100.0%</text>
          <text x="${c}" y="${c + 9}" text-anchor="middle" font-size="7" font-weight="600" fill="var(--tx-muted, #64748b)">CASH</text>
        </svg>
        <div class="tx-donut-legend">
          <div><i class="mini-dot green" style="background:#22c55e;"></i> Settled Cash: ৳${settled.toFixed(0)}</div>
          ${unsettled > 0 ? `<div><i class="mini-dot blue"></i> Unsettled: ৳${unsettled.toFixed(0)}</div>` : ''}
          <div class="muted small">0 Holdings (Clean Slate)</div>
        </div>
      `;
      return;
    }

    const sLen = (settled / total) * circ;
    const uLen = (unsettled / total) * circ;
    const iLen = (invested / total) * circ;
    const sOffset = 0;
    const uOffset = -sLen;
    const iOffset = -(sLen + uLen);

    container.innerHTML = `
      <svg viewBox="0 0 100 100" class="tx-donut-svg">
        <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="var(--tx-border, #1c2837)" stroke-width="12" />
        <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#5de4c7" stroke-width="12"
          stroke-dasharray="${sLen} ${circ - sLen}" stroke-dashoffset="${sOffset}" />
        <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#60a5fa" stroke-width="12"
          stroke-dasharray="${uLen} ${circ - uLen}" stroke-dashoffset="${uOffset}" />
        <circle cx="${c}" cy="${c}" r="${r}" fill="none" stroke="#fbbf24" stroke-width="12"
          stroke-dasharray="${iLen} ${circ - iLen}" stroke-dashoffset="${iOffset}" />
      </svg>
      <div class="tx-donut-legend">
        <div><i class="mini-dot teal"></i> Settled: ৳${settled.toFixed(0)}</div>
        <div><i class="mini-dot blue"></i> Unsettled: ৳${unsettled.toFixed(0)}</div>
        <div><i class="mini-dot amber"></i> Cost: ৳${invested.toFixed(0)}</div>
      </div>
    `;
  }

  // --- 10. Update From Global Snapshot ---
  function updateFromSnapshot(snapshot) {
    if (!snapshot) return;
    state.lastSnapshot = snapshot;

    // Buying Power in Topbar & Ticket
    const bp = snapshot.buying_power_bdt !== undefined ? snapshot.buying_power_bdt : ((snapshot.metrics && snapshot.metrics.available_cash) || 0);
    setText("tx-hdr-buying-power", formatMoney(bp));
    setText("tx-ticket-bp", formatMoney(bp));

    // Gain/Loss in Topbar
    const metrics = snapshot.metrics || {};
    const unPnl = metrics.unrealized_pnl || 0;
    const unPnlPct = metrics.open_cost_basis > 0 ? (unPnl / metrics.open_cost_basis) * 100 : 0;
    const glEl = document.getElementById("tx-hdr-gain-loss");
    if (glEl) {
      glEl.textContent = `${unPnl >= 0 ? "+" : ""}${formatMoney(unPnl)} (${formatPct(unPnlPct)})`;
      glEl.className = `tx-tele-val tabular-nums ${unPnl >= 0 ? "positive" : "negative"}`;
    }

    // Topbar DSEX index
    const dseIdx = snapshot.dse_index;
    const dsexItem = document.getElementById("tx-hdr-dsex-item");
    const dsexVal = document.getElementById("tx-hdr-dsex-val");
    if (dseIdx && dseIdx.dsex_value && dsexItem && dsexVal) {
      dsexItem.style.display = "flex";
      const chgStr = dseIdx.dsex_chg !== undefined ? ` (${Number(dseIdx.dsex_chg) >= 0 ? "+" : ""}${Number(dseIdx.dsex_chg).toFixed(2)})` : "";
      dsexVal.textContent = `${Number(dseIdx.dsex_value).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}${chgStr}`;
      dsexVal.className = `tx-tele-val tabular-nums ${Number(dseIdx.dsex_chg || 0) >= 0 ? "positive" : "negative"}`;
    }

    // Account Summary values
    setText("tx-acc-settled-cash", formatMoney(metrics.available_cash || 0));
    setText("tx-acc-buying-power", formatMoney(bp));
    setText("tx-acc-blocked", "৳0.00");
    setText("tx-acc-unsettled-sales", formatMoney(snapshot.unsettled_sales_bdt || metrics.unsettled_proceeds || 0));
    setText("tx-acc-realized-pnl", formatMoney(metrics.realized_pnl || 0));
    setText("tx-acc-unrealized-pnl", formatMoney(metrics.unrealized_pnl || 0));

    // Live Broker Mirror (H9210) Card values
    const bm = snapshot.broker_mirror_account || {};
    const liveBp = (bm.buying_power !== undefined && bm.buying_power > 0) ? bm.buying_power : (bm.cash_balance || 0);
    setText("tx-bm-cash", formatMoney(bm.cash_balance || 0));
    setText("tx-bm-bp", formatMoney(liveBp || 0));
    setText("tx-bm-unsettled", formatMoney(bm.unsettled_sales || 0));
    setText("tx-bm-withdrawable", formatMoney(bm.cash_available_for_withdrawal || bm.cash_balance || 0));
    if (bm.last_updated) {
      try {
        const d = new Date(bm.last_updated);
        setText("tx-broker-mirror-time", `Updated: ${d.toLocaleTimeString()}`);
      } catch (_) {}
    }

    // Donut chart
    renderAccountDonut(
      metrics.available_cash || 0,
      snapshot.unsettled_sales_bdt || metrics.unsettled_proceeds || 0,
      metrics.open_cost_basis || 0
    );

    // Auto-select first GSC_L1 or held company if not already selected or valid
    if (snapshot.companies && snapshot.companies.length) {
      const exists = snapshot.companies.some((c) => c.symbol === state.selectedSymbol);
      if (!exists || !state.selectedSymbol) {
        const l1 = snapshot.companies.find((c) => c.watchlist_category === "GSC_L1") ||
                   snapshot.companies.find((c) => (c.holding_qty || 0) > 0) ||
                   snapshot.companies[0];
        if (l1) state.selectedSymbol = l1.symbol;
      }
    }

    // Refresh symbol ticket
    selectSymbolForTicket(state.selectedSymbol);
  }

  function setText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  }

  function showToast(msg, isError) {
    if (typeof window.notify === "function") {
      window.notify(msg, isError);
      return;
    }
    const t = document.getElementById("toast");
    if (t) {
      t.textContent = msg;
      t.hidden = false;
      t.style.display = "block";
      setTimeout(() => {
        t.hidden = true;
        t.style.display = "none";
      }, 4000);
    }
  }

  // --- 11. Initialization & Event Binding ---
  function init() {
    // Nav Tabs
    document.querySelectorAll(".tx-nav-tab").forEach((tab) => {
      tab.addEventListener("click", () => switchNavView(tab.dataset.txView));
    });

    // Monitor Tabs
    document.querySelectorAll(".tx-mon-tab").forEach((tab) => {
      tab.addEventListener("click", () => switchMonPane(tab.dataset.monPane));
    });

    // Buy/Sell Toggles
    const buyBtn = document.getElementById("tx-side-buy-btn");
    const sellBtn = document.getElementById("tx-side-sell-btn");
    if (buyBtn) buyBtn.addEventListener("click", () => setOrderSide("BUY"));
    if (sellBtn) sellBtn.addEventListener("click", () => setOrderSide("SELL"));

    // Inputs live calculation
    const qtyInput = document.getElementById("tx-order-qty");
    const priceInput = document.getElementById("tx-order-price");
    if (qtyInput) qtyInput.addEventListener("input", updateOrderTicketCalculations);
    if (priceInput) priceInput.addEventListener("input", updateOrderTicketCalculations);

    // Price step buttons
    const upBtn = document.getElementById("tx-price-up");
    const downBtn = document.getElementById("tx-price-down");
    if (upBtn) {
      upBtn.addEventListener("click", () => {
        const p = parseFloat(priceInput.value) || 0;
        priceInput.value = (p + 0.10).toFixed(2);
        updateOrderTicketCalculations();
      });
    }
    if (downBtn) {
      downBtn.addEventListener("click", () => {
        const p = parseFloat(priceInput.value) || 0;
        priceInput.value = Math.max(0.10, p - 0.10).toFixed(2);
        updateOrderTicketCalculations();
      });
    }

    // Reset button
    const resetBtn = document.getElementById("tx-order-reset-btn");
    if (resetBtn) {
      resetBtn.addEventListener("click", () => {
        if (qtyInput) qtyInput.value = "10";
        selectSymbolForTicket(state.selectedSymbol);
      });
    }

    // Submit order button (Step 1)
    const submitBtn = document.getElementById("tx-order-submit-btn");
    if (submitBtn) submitBtn.addEventListener("click", submitOrderPreview);

    // Confirm Modal actions (Step 2)
    const confirmBtn = document.getElementById("tx-confirm-submit-btn");
    const cancelModalBtn = document.getElementById("tx-confirm-cancel-btn");
    const modal = document.getElementById("tx-confirm-order-modal");

    if (confirmBtn) confirmBtn.addEventListener("click", executeConfirmedOrder);
    if (cancelModalBtn && modal) {
      cancelModalBtn.addEventListener("click", () => modal.close());
    }

    // Filter checkboxes in Market Watch
    const hideZSpot = document.getElementById("filter-hide-z-spot");
    const heldOnly = document.getElementById("filter-held-only");
    if (hideZSpot && typeof window.renderWatchlist === "function") {
      hideZSpot.addEventListener("change", () => window.renderWatchlist());
    }
    if (heldOnly && typeof window.renderWatchlist === "function") {
      heldOnly.addEventListener("change", () => window.renderWatchlist());
    }

    // Shadow Simulator Reset Buttons
    const resetMirrorBtn = document.getElementById("tx-btn-reset-mirror");
    const reset50kBtn = document.getElementById("tx-btn-reset-50k");

    async function handleShadowReset(initialCash, label) {
      try {
        const res = await fetch("/api/tradexpress/shadow/reset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ portfolio_id: "H9210_SHADOW", initial_cash: initialCash }),
        });
        const data = await res.json();
        if (data.status === "RESET_OK") {
          if (typeof window.notify === "function") {
            window.notify(`Shadow Dummy reset: ${label} (৳${initialCash.toLocaleString()})`, false);
          }
          if (typeof window.refreshSnapshot === "function") {
            window.refreshSnapshot();
          }
        } else {
          if (typeof window.notify === "function") {
            window.notify(`Shadow reset failed: ${data.detail || data.error}`, true);
          }
        }
      } catch (err) {
        if (typeof window.notify === "function") {
          window.notify(`Reset error: ${err.message}`, true);
        }
      }
    }

    if (resetMirrorBtn) {
      resetMirrorBtn.addEventListener("click", () => {
        const bm = state.lastSnapshot?.broker_mirror_account;
        const liveCash = (bm && bm.buying_power > 0) ? bm.buying_power : ((bm && bm.cash_balance > 0) ? bm.cash_balance : 353.00);
        handleShadowReset(liveCash, "Mirror H9210 Cash");
      });
    }

    if (reset50kBtn) {
      reset50kBtn.addEventListener("click", () => {
        handleShadowReset(50000.00, "Clean Dummy Capital");
      });
    }

    // Quick prompt chip for Passive Sync Guide
    const passiveGuideChip = document.getElementById("chip-passive-sync-guide");
    if (passiveGuideChip) {
      passiveGuideChip.addEventListener("click", () => {
        const promptText = "Check hb_feed_status and tell me which TradeXpress tabs to click right now";
        const input = document.getElementById("chat-input");
        const form = document.getElementById("chat-form");
        if (input && form) {
          input.value = promptText;
          if (typeof form.requestSubmit === "function") {
            form.requestSubmit();
          } else {
            form.dispatchEvent(new Event("submit", { cancelable: true }));
          }
        }
      });
    }

    // Passive Spy & Bridge Control buttons
    const spyBtn = document.getElementById("tx-passive-spy-btn");
    if (spyBtn) {
      spyBtn.addEventListener("click", () => {
        const isLive = spyBtn.classList.contains("active");
        controlBridge(isLive ? "detach" : "attach");
      });
    }

    const attachBtn = document.getElementById("tx-bridge-attach-btn");
    const detachBtn = document.getElementById("tx-bridge-detach-btn");
    if (attachBtn) attachBtn.addEventListener("click", () => controlBridge("attach"));
    if (detachBtn) detachBtn.addEventListener("click", () => controlBridge("detach"));

    // Quick-qty buttons (25%, 50%, 100%)
    document.querySelectorAll(".tx-quick-qty-strip button[data-pct]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const pct = parseInt(btn.dataset.pct, 10) || 100;
        let baseQty = 10;
        let company = null;
        const comps = state.lastSnapshot?.companies || window.state?.snapshot?.companies || [];
        if (comps && comps.length > 0) {
          company = comps.find((c) => c.symbol === state.selectedSymbol);
        }
        if (state.selectedSide === "SELL") {
          const mature = (company && (company.mature_shares ?? company.mature_qty)) || (company && company.holding_qty) || 0;
          baseQty = Math.max(1, Math.round((mature * pct) / 100));
        } else {
          const bp = (state.lastSnapshot && (state.lastSnapshot.buying_power_bdt || (state.lastSnapshot.metrics && state.lastSnapshot.metrics.available_cash))) ||
                     (window.state && window.state.snapshot && (window.state.snapshot.buying_power_bdt || (window.state.snapshot.metrics && window.state.snapshot.metrics.available_cash))) || 10000;
          const p = parseFloat(priceInput?.value) || (company && (company.last_price ?? company.price)) || 17.50;
          if (p > 0) {
            const maxShares = Math.floor(bp / p);
            baseQty = Math.max(1, Math.floor((maxShares * pct) / 100));
          }
        }
        if (qtyInput) {
          qtyInput.value = String(baseQty);
          updateOrderTicketCalculations();
        }
      });
    });

    // Initial load of orders, feed status & depth table auto-population
    loadOrders();
    loadFeedStatus();
    selectSymbolForTicket(state.selectedSymbol || "BANKASIA");

    // Auto poll orders and feed status
    setInterval(loadOrders, 10000);
    setInterval(loadFeedStatus, 10000);
  }

  // Expose global controller
  window.TradeXpressUI = window.tradexpressUI = {
    init,
    selectSymbol: selectSymbolForTicket,
    selectSymbolForTicket,
    quickSell,
    switchNavView,
    switchMonPane,
    loadOrders,
    loadLearningSummary,
    loadFeedStatus,
    updateFromSnapshot,
    toTradeXpressSymbol,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
