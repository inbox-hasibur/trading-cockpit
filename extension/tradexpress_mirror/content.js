/**
 * Humming Bird — TradeXpress Passive Mirror (Content Script)
 *
 * 100% READ-ONLY PASSIVE DOM READER
 * ZERO-BAN MANDATE: NEVER click, NEVER type/fill, NEVER mutate TradeXpress DOM,
 * NEVER reload/navigate, NEVER read passwords/cookies/tokens, and NEVER send any
 * HTTP/WebSocket requests to broker servers.
 */

(function () {
  'use strict';

  let lastPayloadHash = '';
  let lastHeartbeatTime = 0;
  const READ_INTERVAL_MS = 2500;
  const HEARTBEAT_INTERVAL_MS = 15000;

  function safeText(el) {
    return el && el.innerText ? el.innerText.trim() : '';
  }

  function cleanNum(str) {
    if (!str) return '';
    return String(str).replace(/,/g, '').replace(/%/g, '').trim();
  }

  function parseMoneyValue(text, pattern) {
    if (!text) return 0.0;
    const regex = new RegExp(pattern + '[:\\s\\t]+([0-9,]+(?:\\.[0-9]{1,2})?)', 'i');
    const match = text.match(regex);
    return match ? parseFloat(match[1].replace(/,/g, '')) : 0.0;
  }

  function extractMarketStatus() {
    // Check top-left DSE status indicator or general text
    const statusEl = document.querySelector(
      '.market-status, .dse-status, [data-id="market-status"], .market-state, .header-market-status'
    );
    if (statusEl) {
      const txt = safeText(statusEl).toUpperCase();
      if (txt.includes('SOD') || txt.includes('START OF DAY') || txt.includes('PRE-OPEN') || txt.includes('PRE OPEN')) return 'SOD';
      if (txt.includes('TRADING') || txt.includes('OPEN') || txt.includes('CONTINUOUS')) return 'Trading';
      if (txt.includes('POST') || txt.includes('POST CLOSE') || txt.includes('POST_CLOSE')) return 'Post Close';
      if (txt.includes('CLOSE') || txt.includes('CLOSED')) return 'Close';
    }

    // Fallback regex search on body header
    const headerText = (document.querySelector('header, .app-header, #app-header') || document.body || {}).innerText || '';
    if (/\b(?:SOD|Start\s*of\s*Day|Pre-Open|Pre\s*Open)\b/i.test(headerText)) return 'SOD';
    if (/\b(?:Post\s*Close|Post-Closing)\b/i.test(headerText)) return 'Post Close';
    if (/\b(?:Trading|Continuous\s*Trading)\b/i.test(headerText)) return 'Trading';
    if (/\b(?:Market\s*Closed|Closed|Close)\b/i.test(headerText)) return 'Close';

    return 'Close';
  }

  function extractActiveMarketWatchTab() {
    const activeTab = document.querySelector(
      '#widget-header-8-1-1-2-cached .wdgttl-tab-item.active, #widget-header-8-1-1-2-cached a[role="tab"].active, #widget-header-8-1-1-2-cached [aria-selected="true"]'
    );
    if (activeTab) {
      const txt = safeText(activeTab).toLowerCase();
      if (txt.includes('gsc')) return 'gsc';
      if (txt.includes('l1')) return 'l1';
      if (txt.includes('fav') || txt.includes('my favorites')) return 'favorites';
      if (txt.includes('dhaka') || txt.includes('dse')) return 'market_watch';
      return txt;
    }
    return 'market_watch';
  }

  function extractMarketWatchRows() {
    const rows = [];
    const tableContainer = document.querySelector('#table-8-1-1-2-cached, [container-id="marketWatch"]');
    if (!tableContainer) return rows;

    const leftRows = tableContainer.querySelectorAll('.ember-table-left-table-block .ember-table-table-row');
    const rightRows = tableContainer.querySelectorAll('.ember-table-right-table-block .ember-table-table-row');

    if (leftRows.length > 0 && rightRows.length > 0) {
      // Critical Ember Row Pairing by style.top to prevent virtual scroll displacement
      const leftMap = new Map();
      leftRows.forEach((r) => {
        const topKey = r.style.top || (r.offsetTop + 'px');
        const symEl = r.querySelector('.symbol-fore-color, [cell-id="dataObj.sDes"]');
        const sym = safeText(symEl);
        const hit52 = !!r.querySelector('i.icon-high-low-52, span.wk52-up-icon');
        const jumpUp = !!r.querySelector('i.icon-jump-up');
        if (sym) {
          leftMap.set(topKey, { symbol: sym, hit52, jumpUp });
        }
      });

      rightRows.forEach((r) => {
        const topKey = r.style.top || (r.offsetTop + 'px');
        const leftData = leftMap.get(topKey);
        if (!leftData) return;

        const ltpEl = r.querySelector('[cell-id="dataObj.ltp"]');
        const chgEl = r.querySelector('[cell-id="dataObj.chg"]');
        const pctChgEl = r.querySelector('[cell-id="dataObj.pctChg"]');
        const volEl = r.querySelector('[cell-id="dataObj.vol"]');
        const bbpEl = r.querySelector('[cell-id="dataObj.bbp"]');
        const bbqEl = r.querySelector('[cell-id="dataObj.bbq"]');
        const bapEl = r.querySelector('[cell-id="dataObj.bap"]');
        const baqEl = r.querySelector('[cell-id="dataObj.baq"]');
        const openEl = r.querySelector('[cell-id="dataObj.open"]');
        const highEl = r.querySelector('[cell-id="dataObj.high"]');
        const lowEl = r.querySelector('[cell-id="dataObj.low"]');
        const dlttEl = r.querySelector('[cell-id="dataObj.dltt"]');
        const settEl = r.querySelector('[cell-id="dataObj.dispSettType"]');
        const catEl = r.querySelector('[cell-id="dataObj.dispSymCat"]');

        rows.push({
          sDes: leftData.symbol,
          ltp: cleanNum(safeText(ltpEl)),
          chg: cleanNum(safeText(chgEl)),
          pctChg: cleanNum(safeText(pctChgEl)),
          vol: cleanNum(safeText(volEl)),
          bbp: cleanNum(safeText(bbpEl)),
          bbq: cleanNum(safeText(bbqEl)),
          bap: cleanNum(safeText(bapEl)),
          baq: cleanNum(safeText(baqEl)),
          open: cleanNum(safeText(openEl)),
          high: cleanNum(safeText(highEl)),
          low: cleanNum(safeText(lowEl)),
          dltt: safeText(dlttEl),
          dispSettType: safeText(settEl) || 'PUBLIC',
          dispSymCat: safeText(catEl) || 'A',
          wk52: leftData.hit52,
          jumpUp: leftData.jumpUp,
        });
      });
    } else {
      // Fallback single-block or standard tr scanning
      const directRows = tableContainer.querySelectorAll('.ember-table-table-row, tbody tr');
      directRows.forEach((r) => {
        const symEl = r.querySelector('[cell-id="dataObj.sDes"], .symbol-fore-color');
        const sym = safeText(symEl);
        if (!sym) return;

        const ltpEl = r.querySelector('[cell-id="dataObj.ltp"]');
        const chgEl = r.querySelector('[cell-id="dataObj.chg"]');
        const pctChgEl = r.querySelector('[cell-id="dataObj.pctChg"]');
        const volEl = r.querySelector('[cell-id="dataObj.vol"]');
        const bbpEl = r.querySelector('[cell-id="dataObj.bbp"]');
        const bbqEl = r.querySelector('[cell-id="dataObj.bbq"]');
        const bapEl = r.querySelector('[cell-id="dataObj.bap"]');
        const baqEl = r.querySelector('[cell-id="dataObj.baq"]');
        const openEl = r.querySelector('[cell-id="dataObj.open"]');
        const highEl = r.querySelector('[cell-id="dataObj.high"]');
        const lowEl = r.querySelector('[cell-id="dataObj.low"]');
        const dlttEl = r.querySelector('[cell-id="dataObj.dltt"]');
        const settEl = r.querySelector('[cell-id="dataObj.dispSettType"]');
        const catEl = r.querySelector('[cell-id="dataObj.dispSymCat"]');
        const hit52 = !!r.querySelector('i.icon-high-low-52, span.wk52-up-icon');
        const jumpUp = !!r.querySelector('i.icon-jump-up');

        rows.push({
          sDes: sym,
          ltp: cleanNum(safeText(ltpEl)),
          chg: cleanNum(safeText(chgEl)),
          pctChg: cleanNum(safeText(pctChgEl)),
          vol: cleanNum(safeText(volEl)),
          bbp: cleanNum(safeText(bbpEl)),
          bbq: cleanNum(safeText(bbqEl)),
          bap: cleanNum(safeText(bapEl)),
          baq: cleanNum(safeText(baqEl)),
          open: cleanNum(safeText(openEl)),
          high: cleanNum(safeText(highEl)),
          low: cleanNum(safeText(lowEl)),
          dltt: safeText(dlttEl),
          dispSettType: safeText(settEl) || 'PUBLIC',
          dispSymCat: safeText(catEl) || 'A',
          wk52: hit52,
          jumpUp: jumpUp,
        });
      });
    }

    return rows;
  }

  function extractOrderTicketLimits() {
    const ticket = document.querySelector('#order-ticket-landscape-id, [container-id="orderTicket"]');
    if (!ticket || ticket.offsetParent === null) return null;

    // Symbol from header #widget-header-8-1-1-1 (e.g. "New Order - BANKASIA`PB (DSE)")
    let symbol = '';
    const headerEl = ticket.querySelector('#widget-header-8-1-1-1, .widget-header');
    if (headerEl) {
      const match = safeText(headerEl).match(/-\s*([A-Za-z0-9_`']+)/i);
      if (match) symbol = match[1].trim();
    }

    // Min / Max limits from [data-id="order-price-info-level-4"]
    let minLimit = null;
    let maxLimit = null;
    const limitsEl = ticket.querySelector('#order-symbol-info [data-id="order-price-info-level-4"], [data-id="order-price-info-level-4"]');
    if (limitsEl) {
      const text = safeText(limitsEl);
      const minMatch = text.match(/min[:\s\t]*([0-9,]+(?:\.[0-9]{1,2})?)/i);
      const maxMatch = text.match(/max[:\s\t]*([0-9,]+(?:\.[0-9]{1,2})?)/i);
      if (minMatch) minLimit = parseFloat(minMatch[1].replace(/,/g, ''));
      if (maxMatch) maxLimit = parseFloat(maxMatch[1].replace(/,/g, ''));
    }

    // Buying power
    const bpEl = ticket.querySelector('[data-id="bp-short"] .holding-trade-bp, .holding-trade-bp');
    const buyingPower = bpEl ? parseFloat(cleanNum(safeText(bpEl))) || 0.0 : null;

    if (!symbol && minLimit === null && maxLimit === null && buyingPower === null) {
      return null;
    }

    return {
      symbol: symbol || '',
      min_limit: minLimit,
      max_limit: maxLimit,
      buying_power: buyingPower,
    };
  }

  function extractPortfolioAndAccountSummary() {
    const portContainer = document.querySelector('#portfolioContainer-8-1-2-3, [container-id="portfolio"]');
    const result = {
      portfolio_rows: [],
      account_summary: null,
      active_tab: 'portfolio',
    };

    if (!portContainer) return result;

    const activeTabEl = portContainer.querySelector(
      'a.active[container-tab-id], .nav-tabs .active a, [role="tab"].active, [aria-selected="true"]'
    );
    const activeTabAttr = activeTabEl ? (activeTabEl.getAttribute('container-tab-id') || safeText(activeTabEl)).toLowerCase() : '';

    if (activeTabAttr.includes('account')) {
      result.active_tab = 'account_summary';
    } else if (activeTabAttr.includes('order')) {
      result.active_tab = 'order_list';
    } else {
      result.active_tab = 'portfolio';
    }

    // 1. Portfolio Rows if portfolio tab or rows exist
    const leftRows = portContainer.querySelectorAll('.ember-table-left-table-block .ember-table-table-row');
    const rightRows = portContainer.querySelectorAll('.ember-table-right-table-block .ember-table-table-row');

    if (leftRows.length > 0 && rightRows.length > 0) {
      const leftMap = new Map();
      leftRows.forEach((r) => {
        const topKey = r.style.top || (r.offsetTop + 'px');
        const symEl = r.querySelector('[cell-id="symbolInfo.dSym"], .symbol-fore-color');
        const sym = safeText(symEl);
        if (sym) leftMap.set(topKey, sym);
      });

      rightRows.forEach((r) => {
        const topKey = r.style.top || (r.offsetTop + 'px');
        const sym = leftMap.get(topKey);
        if (!sym) return;

        const totalEl = r.querySelector('[cell-id="profLossQty"]');
        const availEl = r.querySelector('[cell-id="avaiQtyDSE"]');
        const penEl = r.querySelector('[cell-id="penHolding"]');
        const buyEl = r.querySelector('[cell-id="pendBuy"]');
        const sellEl = r.querySelector('[cell-id="pendSell"]');
        const avgCostEl = r.querySelector('[cell-id="avgCst"]');
        const mktPriceEl = r.querySelector('[cell-id="mktPrice"]');

        result.portfolio_rows.push({
          symbol: sym,
          total_qty: cleanNum(safeText(totalEl)),
          available_qty: cleanNum(safeText(availEl)),
          pending_qty: cleanNum(safeText(penEl)),
          buy_pending_qty: cleanNum(safeText(buyEl)),
          sell_pending_qty: cleanNum(safeText(sellEl)),
          average_cost: cleanNum(safeText(avgCostEl)),
          market_price: cleanNum(safeText(mktPriceEl)),
        });
      });
    } else {
      const genericRows = portContainer.querySelectorAll('tbody tr, .ember-table-table-row');
      genericRows.forEach((r) => {
        const symEl = r.querySelector('[cell-id="symbolInfo.dSym"], .symbol-fore-color');
        const sym = safeText(symEl);
        if (!sym) return;

        const totalEl = r.querySelector('[cell-id="profLossQty"]');
        const availEl = r.querySelector('[cell-id="avaiQtyDSE"]');
        const penEl = r.querySelector('[cell-id="penHolding"]');
        const avgCostEl = r.querySelector('[cell-id="avgCst"]');
        const mktPriceEl = r.querySelector('[cell-id="mktPrice"]');

        result.portfolio_rows.push({
          symbol: sym,
          total_qty: cleanNum(safeText(totalEl)),
          available_qty: cleanNum(safeText(availEl)),
          pending_qty: cleanNum(safeText(penEl)),
          average_cost: cleanNum(safeText(avgCostEl)),
          market_price: cleanNum(safeText(mktPriceEl)),
        });
      });
    }

    // 2. Account Summary Text/Cells (always check container or full text)
    const containerText = portContainer.innerText || '';
    const cash = parseMoneyValue(containerText, '(?:Cash Balance|Available Cash)');
    const availCash = parseMoneyValue(containerText, 'Available Cash Balance') || cash;
    const buyingPower = parseMoneyValue(containerText, '(?:Buying Power|Purchasing Power)');
    const blocked = parseMoneyValue(containerText, '(?:Blocked Amount|Blocked Cash)');
    const unsettled = parseMoneyValue(containerText, '(?:Unsettled Sales|Unsettled Amount)');
    const payable = parseMoneyValue(containerText, 'Payable Amount');

    if (cash > 0 || buyingPower > 0 || unsettled > 0 || blocked > 0 || payable > 0) {
      result.account_summary = {
        cash_balance: cash,
        available_cash_balance: availCash,
        blocked_amount: blocked,
        cash_available_for_withdrawal: cash,
        unsettled_sales: unsettled,
        payable_amount: payable,
        buying_power: buyingPower > 0 ? buyingPower : (cash + unsettled),
      };
    }

    return result;
  }

  function runPassiveRead() {
    chrome.storage.local.get({ mirrorEnabled: true }, (settings) => {
      if (!settings.mirrorEnabled) return;

      try {
        const dseStatus = extractMarketStatus();
        const mwTab = extractActiveMarketWatchTab();
        const mwRows = extractMarketWatchRows();
        const ticketLimits = extractOrderTicketLimits();
        const portData = extractPortfolioAndAccountSummary();

        // Effective active tab
        const activeTab = portData.active_tab !== 'portfolio' ? portData.active_tab : mwTab;

        // Account summary fallback to ticket buying power if present
        let acctSummary = portData.account_summary;
        if (!acctSummary && ticketLimits && ticketLimits.buying_power !== null && ticketLimits.buying_power > 0) {
          acctSummary = {
            cash_balance: ticketLimits.buying_power,
            available_cash_balance: ticketLimits.buying_power,
            buying_power: ticketLimits.buying_power,
            blocked_amount: 0,
            unsettled_sales: 0,
            payable_amount: 0,
          };
        }

        const payload = {
          source: 'EDGE_EXTENSION_PASSIVE',
          timestamp: new Date().toISOString(),
          dse_status: dseStatus,
          tab: activeTab,
          market_watch_rows: mwRows,
          portfolio_rows: portData.portfolio_rows,
          account_summary: acctSummary,
          order_ticket_limits: ticketLimits,
        };

        // Create structural fingerprint (excluding timestamp)
        const fingerprintPayload = {
          dse_status: dseStatus,
          tab: activeTab,
          rows_len: mwRows.length,
          mw_first: mwRows[0] || null,
          mw_last: mwRows[mwRows.length - 1] || null,
          pf_len: portData.portfolio_rows.length,
          acct: acctSummary,
          limits: ticketLimits,
        };
        const fingerprint = JSON.stringify(fingerprintPayload);
        const now = Date.now();
        const isHeartbeat = (now - lastHeartbeatTime) >= HEARTBEAT_INTERVAL_MS;

        if (fingerprint !== lastPayloadHash || isHeartbeat) {
          lastPayloadHash = fingerprint;
          lastHeartbeatTime = now;

          chrome.runtime.sendMessage(
            { type: 'PASSIVE_SNAPSHOT', payload },
            () => {
              // Silently handle response or disconnect
              if (chrome.runtime.lastError) {
                // Background worker might be idle or unavailable
              }
            }
          );
        }
      } catch (err) {
        // 100% fail-safe: never crash or interfere with TradeXpress host page
      }
    });
  }

  // Initial read and periodic loop
  setTimeout(runPassiveRead, 1000);
  setInterval(runPassiveRead, READ_INTERVAL_MS);

  // Passive Network Tap Event Queue (relayed from MAIN world network_tap.js)
  const netTapQueue = [];
  let netTapFlushTimer = null;

  function flushNetTapQueue() {
    if (netTapQueue.length === 0) return;
    const batch = netTapQueue.splice(0, netTapQueue.length);
    try {
      chrome.runtime.sendMessage({
        type: 'PASSIVE_NET_BATCH',
        events: batch,
      });
    } catch (_) {}
  }

  window.addEventListener('message', function (evt) {
    if (evt.source !== window || !evt.data || !evt.data.__hbPassiveNet) return;
    try {
      const event = evt.data.event;
      if (event) {
        netTapQueue.push(event);
        if (netTapQueue.length >= 25) {
          if (netTapFlushTimer) clearTimeout(netTapFlushTimer);
          netTapFlushTimer = null;
          flushNetTapQueue();
        } else if (!netTapFlushTimer) {
          netTapFlushTimer = setTimeout(function () {
            netTapFlushTimer = null;
            flushNetTapQueue();
          }, 1500);
        }
      }
    } catch (_) {}
  });
})();
