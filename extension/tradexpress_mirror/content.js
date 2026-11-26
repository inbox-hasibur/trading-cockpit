/**
 * Humming Bird — TradeXpress Passive Mirror (Content Script)
 *
 * 100% READ-ONLY PASSIVE DOM READER
 * ZERO-BAN MANDATE: NEVER click, NEVER type/fill, NEVER mutate TradeXpress DOM,
 * NEVER reload/navigate, NEVER read passwords/cookies/tokens, and NEVER send any
 * HTTP/WebSocket requests to broker servers.
 *
 * Sprint 5F Upgrade:
 * - 0.35s trailing debounce MutationObserver for sub-second near-realtime price streaming.
 * - Accurate active_tab extraction (Dhaka Stock Exchange, My Favorites, GSC, L1, L2).
 * - Real 5-Level Order Book Depth from Order Ticket (#order-ticket-landscape-id).
 * - Real DSEX Index & Market Breadth (Advances/Declines/Unchanged).
 */

(function () {
  'use strict';

  let lastPayloadHash = '';
  let lastHeartbeatTime = 0;
  let debounceTimer = null;
  const DEBOUNCE_DELAY_MS = 350;
  const HEARTBEAT_INTERVAL_MS = 5000;

  function safeText(el) {
    return el && el.innerText ? el.innerText.trim() : '';
  }

  function cleanNum(str) {
    if (!str) return '';
    return String(str)
      .replace(/,/g, '')
      .replace(/%/g, '')
      .replace(/\+/g, '')
      .replace(/BDT/gi, '')
      .replace(/৳/g, '')
      .trim();
  }

  function extractGlobalBuyingPower() {
    // Tier 1: Order ticket top panel Buying Power box
    const bpPanelEl = document.querySelector(
      '#order-top-panel-8-1-1-1 [data-id="bp-short"] .holding-trade-bp, ' +
      '#order-ticket-landscape-id [data-id="bp-short"] .holding-trade-bp, ' +
      '[data-id="bp-short"] .holding-trade-bp, ' +
      '.holding-trade-bp'
    );
    if (bpPanelEl) {
      const v = parseFloat(cleanNum(safeText(bpPanelEl)));
      if (!isNaN(v) && v > 0) return v;
    }

    // Tier 2: Top header navbar - find element matching "Buying Power" and grab numeric value in parent/sibling container
    const headerContainers = document.querySelectorAll(
      'header, .app-header, #app-header, .top-bar, .tx-topbar, #top-bar, nav, .header, #header'
    );
    for (const h of headerContainers) {
      const allDescendants = h.querySelectorAll('*');
      for (const el of allDescendants) {
        if (/^Buying\s*Power$/i.test(safeText(el))) {
          const parent = el.parentElement;
          if (parent) {
            const m = safeText(parent).match(/([0-9,]+(?:\.[0-9]{1,2})?)/);
            if (m) {
              const num = parseFloat(m[1].replace(/,/g, ''));
              if (!isNaN(num) && num > 0) return num;
            }
          }
        }
      }
      const text = safeText(h);
      const bpMatch = text.match(/Buying\s*Power[:\s\t]+(?:BDT|৳)?\s*([0-9,]+(?:\.[0-9]{1,2})?)/i);
      if (bpMatch) {
        const v = parseFloat(bpMatch[1].replace(/,/g, ''));
        if (!isNaN(v) && v > 0) return v;
      }
    }

    return null;
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
    const headerText = (document.querySelector('header, .app-header, #app-header, .top-bar') || document.body || {}).innerText || '';
    if (/\b(?:SOD|Start\s*of\s*Day|Pre-Open|Pre\s*Open)\b/i.test(headerText)) return 'SOD';
    if (/\b(?:Post\s*Close|Post-Closing)\b/i.test(headerText)) return 'Post Close';
    if (/\b(?:Trading|Continuous\s*Trading)\b/i.test(headerText)) return 'Trading';
    if (/\b(?:Market\s*Closed|Closed|Close)\b/i.test(headerText)) return 'Close';

    return 'Close';
  }

  function extractActiveMarketWatchTab() {
    const activeEl = document.querySelector(
      '#widget-header-8-1-1-2-cached li.active a, ' +
      '#widget-header-8-1-1-2-cached a.active, ' +
      '#widget-header-8-1-1-2-cached a[role="tab"].active, ' +
      '#widget-header-8-1-1-2-cached .wdgttl-tab-item.active, ' +
      '#widget-header-8-1-1-2-cached [aria-selected="true"], ' +
      '#widget-header-8-1-1-2-cached .active'
    );
    if (activeEl) {
      const rawText = safeText(activeEl);
      const txt = rawText.toLowerCase();
      if (txt.includes('dhaka') || txt.includes('dse')) return 'Dhaka Stock Exchange';
      if (txt.includes('fav') || txt.includes('my favorites')) return 'My Favorites';
      if (txt.includes('gsc_l1') || txt === 'l1' || txt.includes(' l1')) return 'L1';
      if (txt.includes('gsc_l2') || txt === 'l2' || txt.includes(' l2')) return 'L2';
      if (txt.includes('gsc')) return 'GSC';
      if (rawText) return rawText;
    }
    return 'Dhaka Stock Exchange';
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
      // Fallback single-block parsing
      const singleRows = tableContainer.querySelectorAll('.ember-table-table-row');
      singleRows.forEach((r) => {
        const symEl = r.querySelector('.symbol-fore-color, [cell-id="dataObj.sDes"]');
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

  function extractOrderTicketLimitsAndDepth() {
    const ticket = document.querySelector('#order-ticket-landscape-id, [container-id="orderTicket"]');
    if (!ticket || ticket.offsetParent === null) return { limits: null, depth: null };

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

    let limits = null;
    if (symbol || minLimit !== null || maxLimit !== null || buyingPower !== null) {
      limits = {
        symbol: symbol || '',
        min_limit: minLimit,
        max_limit: maxLimit,
        buying_power: buyingPower,
      };
    }

    // Extract Real 5-Level Market Depth from Order Ticket depth rows
    let depth = null;
    let depthTable = null;

    // Locate the depth table whose thead or header rows contain Quantity + Bid + Offer
    const candidateTables = ticket.querySelectorAll('table, .order-ticket-depth, [data-id="depth-table"], .depth-table');
    for (const t of candidateTables) {
      const headerText = (t.querySelector('thead') || t).innerText.toLowerCase();
      if ((headerText.includes('bid') || headerText.includes('buy')) && (headerText.includes('offer') || headerText.includes('ask') || headerText.includes('sell'))) {
        depthTable = t;
        break;
      }
    }
    if (!depthTable) {
      depthTable = ticket.querySelector('.order-ticket-depth-table, [data-id="depth-table"], table.depth-table, .order-depth, #order-depth');
    }

    const rows = (depthTable || ticket).querySelectorAll('tbody tr, .depth-row, tr');
    const levels = [];
    rows.forEach((r) => {
      if (r.querySelector('th')) return; // skip thead rows
      const cells = r.querySelectorAll('td, .depth-cell, [cell-id]');
      if (cells.length >= 4) {
        const bQty = parseInt(cleanNum(safeText(cells[0]))) || 0;
        const bPrice = parseFloat(cleanNum(safeText(cells[1]))) || 0.0;
        const oPrice = parseFloat(cleanNum(safeText(cells[2]))) || 0.0;
        const oQty = parseInt(cleanNum(safeText(cells[3]))) || 0;
        if (bPrice > 0 || oPrice > 0 || bQty > 0 || oQty > 0) {
          levels.push({
            bid_qty: bQty,
            bid: bPrice,
            offer: oPrice,
            offer_qty: oQty,
          });
        }
      }
    });

    if (levels.length > 0 && symbol) {
      depth = {
        symbol: symbol,
        levels: levels.slice(0, 5),
      };
    }

    return { limits, depth };
  }

  function extractMarketIndex() {
    let dsex = null, dsexChg = null, dsexPct = null;
    let up = null, down = null, unch = null;

    // Direct selectors
    const dsexEl = document.querySelector('.dsex-value, [data-id="dsex-value"], .index-dsex, [data-symbol="DSEX"]');
    if (dsexEl) {
      dsex = parseFloat(cleanNum(safeText(dsexEl))) || null;
    }
    const upEl = document.querySelector('.advances-count, .up-count, [data-id="up-count"], .market-up');
    if (upEl) up = parseInt(cleanNum(safeText(upEl))) || null;
    const downEl = document.querySelector('.declines-count, .down-count, [data-id="down-count"], .market-down');
    if (downEl) down = parseInt(cleanNum(safeText(downEl))) || null;
    const unchEl = document.querySelector('.unchanged-count, [data-id="unch-count"], .market-unch');
    if (unchEl) unch = parseInt(cleanNum(safeText(unchEl))) || null;

    // Header text scan fallback
    const headerText = (document.querySelector('header, .app-header, #app-header, .top-bar, .market-summary') || document.body || {}).innerText || '';

    if (dsex === null) {
      const dsexMatch = headerText.match(/DSEX[:\s\t]+([0-9,]+(?:\.[0-9]{1,2})?)/i);
      if (dsexMatch) dsex = parseFloat(dsexMatch[1].replace(/,/g, ''));
    }
    const chgMatch = headerText.match(/DSEX[^\n\r]*?([+-]?[0-9,]+(?:\.[0-9]{1,2})?)\s*\(\s*([+-]?[0-9.]+)%\s*\)/i);
    if (chgMatch) {
      dsexChg = parseFloat(chgMatch[1].replace(/,/g, ''));
      dsexPct = parseFloat(chgMatch[2]);
    }
    if (up === null) {
      const m = headerText.match(/\b(?:Up|Advances|▲)[:\s\t]*(\d+)\b/i);
      if (m) up = parseInt(m[1]);
    }
    if (down === null) {
      const m = headerText.match(/\b(?:Down|Declines|▼)[:\s\t]*(\d+)\b/i);
      if (m) down = parseInt(m[1]);
    }
    if (unch === null) {
      const m = headerText.match(/\b(?:Unch(?:anged)?|=|Un-changed)[:\s\t]*(\d+)\b/i);
      if (m) unch = parseInt(m[1]);
    }

    if (dsex === null && up === null && down === null && unch === null) return null;
    return {
      dsex_value: dsex,
      dsex_chg: dsexChg,
      dsex_pct_chg: dsexPct,
      up_count: up,
      down_count: down,
      unchanged_count: unch,
    };
  }

  function extractPortfolioAndAccountSummary() {
    const portContainer = document.querySelector('#portfolioContainer-8-1-2-3, [container-id="portfolio"]');
    const result = {
      portfolio_rows: [],
      broker_order_list: [],
      account_summary: null,
      active_tab: 'portfolio',
    };

    const globalBp = extractGlobalBuyingPower();

    let summaryScope = null;
    if (portContainer) {
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

      // 1. Header-mapped Ember Table scraper for Order List & Portfolio
      const leftHeaderCells = Array.from(
        portContainer.querySelectorAll('.ember-table-left-table-block .ember-table-header-row .ember-table-header-cell, .ember-table-left-table-block .ember-table-header-cell')
      );
      const rightHeaderCells = Array.from(
        portContainer.querySelectorAll('.ember-table-right-table-block .ember-table-header-row .ember-table-header-cell, .ember-table-right-table-block .ember-table-header-cell')
      );
      const normHdr = (s) => String(s || '').toLowerCase().replace(/\s+/g, ' ').trim();
      const rightHeaders = rightHeaderCells.map((h) => normHdr(safeText(h)));
      const looksLikeOrderList = rightHeaders.some((h) => h.includes('order id') || h.includes('filled') || h.includes('pending qty') || h.includes('pending quantity') || h === 'side');
      if (looksLikeOrderList) {
        result.active_tab = 'order_list';
      }

      const leftRows = portContainer.querySelectorAll('.ember-table-left-table-block .ember-table-table-row');
      const rightRows = portContainer.querySelectorAll('.ember-table-right-table-block .ember-table-table-row');

      if (leftRows.length > 0 && rightRows.length > 0) {
        const leftByTop = new Map();
        const leftByIdx = [];
        leftRows.forEach((r, idx) => {
          const topKey = r.style.top || (r.offsetTop + 'px');
          const symEl = r.querySelector('[cell-id="dataObj.symbolInfo.dSym"], [cell-id="dataObj.sDes"], [cell-id="dataObj.symbol"], .symbol-fore-color') || r.querySelector('.ember-table-cell');
          const sym = safeText(symEl);
          if (sym) {
            leftByTop.set(topKey, sym);
            leftByIdx[idx] = sym;
          }
        });

        const pickByHeaderOrSelector = (row, selectors, headerMatchers) => {
          for (const sel of selectors) {
            const el = row.querySelector(sel);
            if (el) {
              const txt = safeText(el);
              if (txt) return txt;
            }
          }
          if (rightHeaders.length > 0) {
            const cells = Array.from(row.querySelectorAll('.ember-table-cell'));
            for (let i = 0; i < rightHeaders.length && i < cells.length; i++) {
              const hdr = rightHeaders[i];
              if (headerMatchers.some((m) => hdr.includes(m))) {
                return safeText(cells[i]);
              }
            }
          }
          return '';
        };

        rightRows.forEach((r, idx) => {
          const topKey = r.style.top || (r.offsetTop + 'px');
          const sym = leftByTop.get(topKey) || leftByIdx[idx];
          if (!sym) return;

          if (result.active_tab === 'order_list') {
            const ordId = pickByHeaderOrSelector(r, ['[cell-id="dataObj.orderId"]', '[cell-id="dataObj.ordId"]', '[cell-id="dataObj.refNo"]'], ['order id', 'ord id', 'ref']);
            const cash = pickByHeaderOrSelector(r, ['[cell-id="dataObj.cashAccount"]', '[cell-id="dataObj.clientCode"]'], ['cash a/c', 'cash', 'client']);
            const stat = pickByHeaderOrSelector(r, ['[cell-id="dataObj.ordStatus"]', '[cell-id="dataObj.status"]'], ['status']);
            const side = pickByHeaderOrSelector(r, ['[cell-id="dataObj.side"]', '[cell-id="dataObj.ordSide"]'], ['side']);
            const qty = pickByHeaderOrSelector(r, ['[cell-id="dataObj.ordQty"]', '[cell-id="dataObj.qty"]'], ['quantity', 'qty']);
            const price = pickByHeaderOrSelector(r, ['[cell-id="dataObj.ordPrice"]', '[cell-id="dataObj.price"]'], ['price']);
            const fill = pickByHeaderOrSelector(r, ['[cell-id="dataObj.filledQty"]', '[cell-id="dataObj.execQty"]'], ['filled']);
            const pend = pickByHeaderOrSelector(r, ['[cell-id="dataObj.pendingQty"]', '[cell-id="dataObj.leavesQty"]'], ['pending']);
            const avg = pickByHeaderOrSelector(r, ['[cell-id="dataObj.avgPrice"]'], ['avg']);
            const val = pickByHeaderOrSelector(r, ['[cell-id="dataObj.orderValue"]', '[cell-id="dataObj.ordVal"]'], ['order value', 'value']);

            result.broker_order_list.push({
              symbol: sym,
              orderId: ordId,
              cashAccount: cash || 'H9210',
              status: stat,
              side: side,
              quantity: parseNum(qty) || 0,
              price: parseNum(price) || 0,
              filledQty: parseNum(fill) || 0,
              pendingQty: parseNum(pend) || 0,
              avgPrice: parseNum(avg) || 0,
              orderValue: parseNum(val) || 0,
            });
            return;
          }

          const totalQty = pickByHeaderOrSelector(r, ['[cell-id="dataObj.profLossQty"]'], ['quantity', 'total qty']);
          const avaiQty = pickByHeaderOrSelector(r, ['[cell-id="dataObj.avaiQtyDSE"]'], ['available qty']);
          const penHolding = pickByHeaderOrSelector(r, ['[cell-id="dataObj.penHolding"]'], ['pending holding']);
          const pendBuy = pickByHeaderOrSelector(r, ['[cell-id="dataObj.pendBuy"]'], ['buy pending']);
          const pendSell = pickByHeaderOrSelector(r, ['[cell-id="dataObj.pendSell"]'], ['sell pending']);
          const avgCst = pickByHeaderOrSelector(r, ['[cell-id="dataObj.avgCst"]'], ['avg. cost', 'avg cost']);
          const mktPrice = pickByHeaderOrSelector(r, ['[cell-id="dataObj.mktPrice"]'], ['market price']);

          result.portfolio_rows.push({
            symbol: sym,
            total_qty: parseInt(cleanNum(totalQty)) || 0,
            available_dse_qty: parseInt(cleanNum(avaiQty)) || 0,
            pending_holding_qty: parseInt(cleanNum(penHolding)) || 0,
            buy_pending_qty: parseInt(cleanNum(pendBuy)) || 0,
            sell_pending_qty: parseInt(cleanNum(pendSell)) || 0,
            avg_cost: cleanNum(avgCst),
            market_price: cleanNum(mktPrice),
          });
        });
      }

      summaryScope = portContainer.querySelector(
        '.account-summary-container, [container-id="accountSummary"], .account-summary, #account-summary, [data-id="account-summary"]'
      ) || portContainer;
    } else {
      summaryScope = document.querySelector(
        '.account-summary-container, [container-id="accountSummary"], .account-summary, #account-summary'
      );
    }

    // 2. Resilient Label-Based Account Summary Extraction
    const labelValues = {};
    const candidateRows = (summaryScope || document).querySelectorAll(
      'tr, .ember-table-table-row, .account-row, .kv-row, div.row, div'
    );

    const patterns = [
      { key: 'customer_number', regex: /Customer\s*Number/i },
      { key: 'cash_balance', regex: /Cash\s*Balance|Ledger\s*Balance/i },
      { key: 'available_cash_balance', regex: /Available\s*Cash(?:\s*Balance)?/i },
      { key: 'blocked_amount', regex: /Blocked\s*Amount/i },
      { key: 'cash_available_for_withdrawal', regex: /Cash\s*Available\s*For\s*Withdrawal/i },
      { key: 'unsettled_sales', regex: /Unsettled\s*Sales/i },
      { key: 'payable_amount', regex: /Payable\s*Amount/i },
      { key: 'buying_power', regex: /Buying\s*Power/i },
    ];

    candidateRows.forEach((row) => {
      const text = safeText(row);
      if (!text || text.length > 200) return;

      patterns.forEach(({ key, regex }) => {
        if (labelValues[key] !== undefined) return;
        if (regex.test(text)) {
          const cells = row.querySelectorAll('td, .table-cell, .col, span, div');
          if (cells.length >= 2) {
            for (let i = 0; i < cells.length; i++) {
              if (regex.test(safeText(cells[i]))) {
                for (let j = i + 1; j < cells.length; j++) {
                  const valTxt = cleanNum(safeText(cells[j]));
                  if (valTxt && /^[0-9]+(?:\.[0-9]{1,2})?$/.test(valTxt)) {
                    labelValues[key] = key === 'customer_number' ? valTxt : parseFloat(valTxt);
                    break;
                  }
                }
                break;
              }
            }
          }
          if (labelValues[key] === undefined) {
            const m = text.match(new RegExp(regex.source + '[:\\s\\t]+(?:BDT|৳)?\\s*([0-9,]+(?:\\.[0-9]{1,2})?)', 'i'));
            if (m) {
              const numStr = m[1].replace(/,/g, '');
              labelValues[key] = key === 'customer_number' ? numStr : parseFloat(numStr);
            }
          }
        }
      });
    });

    const cash = labelValues.cash_balance !== undefined ? labelValues.cash_balance : 0.0;
    const availCash = labelValues.available_cash_balance !== undefined ? labelValues.available_cash_balance : cash;
    const blocked = labelValues.blocked_amount !== undefined ? labelValues.blocked_amount : 0.0;
    const unsettled = labelValues.unsettled_sales !== undefined ? labelValues.unsettled_sales : 0.0;
    const payable = labelValues.payable_amount !== undefined ? labelValues.payable_amount : 0.0;
    const withdrawable = labelValues.cash_available_for_withdrawal !== undefined ? labelValues.cash_available_for_withdrawal : cash;
    const bp = labelValues.buying_power !== undefined && labelValues.buying_power > 0
      ? labelValues.buying_power
      : (globalBp !== null && globalBp > 0 ? globalBp : (availCash > 0 ? availCash : (cash + unsettled)));

    if (bp > 0 || cash > 0 || availCash > 0 || unsettled > 0 || blocked > 0 || (globalBp !== null && globalBp > 0)) {
      result.account_summary = {
        customer_number: labelValues.customer_number || 'H9210',
        cash_balance: cash,
        available_cash_balance: availCash,
        blocked_amount: blocked,
        cash_available_for_withdrawal: withdrawable,
        unsettled_sales: unsettled,
        payable_amount: payable,
        buying_power: bp,
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
        const { limits: ticketLimits, depth: ticketDepth } = extractOrderTicketLimitsAndDepth();
        const marketIndex = extractMarketIndex();
        const portData = extractPortfolioAndAccountSummary();

        // Effective active tab
        const activeTab = portData.active_tab !== 'portfolio' ? portData.active_tab : mwTab;

        // Account summary fallback to ticket buying power or globalBp if present
        let acctSummary = portData.account_summary;
        const globalBp = extractGlobalBuyingPower();
        const effectiveBp = (ticketLimits && ticketLimits.buying_power !== null && ticketLimits.buying_power > 0) ? ticketLimits.buying_power : globalBp;
        if (!acctSummary && effectiveBp !== null && effectiveBp > 0) {
          acctSummary = {
            customer_number: 'H9210',
            cash_balance: effectiveBp,
            available_cash_balance: effectiveBp,
            buying_power: effectiveBp,
            blocked_amount: 0,
            unsettled_sales: 0,
            payable_amount: 0,
            cash_available_for_withdrawal: effectiveBp,
          };
        } else if (acctSummary) {
          if ((!acctSummary.buying_power || acctSummary.buying_power === 0) && effectiveBp !== null && effectiveBp > 0) {
            acctSummary.buying_power = effectiveBp;
          }
          if ((!acctSummary.cash_balance || acctSummary.cash_balance === 0) && effectiveBp !== null && effectiveBp > 0) {
            acctSummary.buying_power = effectiveBp;
          }
        }

        const payload = {
          source: 'EDGE_EXTENSION_PASSIVE',
          timestamp: new Date().toISOString(),
          dse_status: dseStatus,
          tab: activeTab,
          market_watch_rows: mwRows,
          portfolio_rows: portData.portfolio_rows,
          broker_order_list: portData.broker_order_list || [],
          account_summary: acctSummary,
          order_ticket_limits: ticketLimits,
          order_ticket_depth: ticketDepth,
          market_index: marketIndex,
        };

        // Structural fingerprint to prevent duplicate transmits
        const fingerprintPayload = {
          dse_status: dseStatus,
          tab: activeTab,
          rows_len: mwRows.length,
          mw_first: mwRows[0] || null,
          mw_last: mwRows[mwRows.length - 1] || null,
          pf_len: portData.portfolio_rows.length,
          ord_len: (portData.broker_order_list || []).length,
          acct: acctSummary,
          limits: ticketLimits,
          depth: ticketDepth,
          idx: marketIndex,
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

  function schedulePassiveRead() {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      debounceTimer = null;
      runPassiveRead();
    }, DEBOUNCE_DELAY_MS);
  }

  // Setup MutationObserver on market watch table and order ticket
  function initMutationObservers() {
    if (!window.MutationObserver) return;
    const observer = new MutationObserver(() => {
      schedulePassiveRead();
    });

    const targetSelectors = [
      '#table-8-1-1-2-cached',
      '[container-id="marketWatch"]',
      '#order-ticket-landscape-id',
      '[container-id="orderTicket"]',
      '#portfolioContainer-8-1-2-3',
      '#widget-header-8-1-1-2-cached',
      'header',
      '.app-header',
    ];

    targetSelectors.forEach((sel) => {
      const el = document.querySelector(sel);
      if (el) {
        observer.observe(el, {
          childList: true,
          subtree: true,
          characterData: true,
        });
        el.__hbObserved = true;
      }
    });

    // Body observer for dynamic DOM mounting
    const bodyObserver = new MutationObserver(() => {
      targetSelectors.forEach((sel) => {
        const el = document.querySelector(sel);
        if (el && !el.__hbObserved) {
          el.__hbObserved = true;
          observer.observe(el, { childList: true, subtree: true, characterData: true });
        }
      });
    });
    bodyObserver.observe(document.body || document.documentElement, { childList: true, subtree: true });
  }

  // Start initial read, observers, and heartbeat
  setTimeout(runPassiveRead, 500);
  initMutationObservers();
  setInterval(runPassiveRead, HEARTBEAT_INTERVAL_MS);

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
          }, 500); // 500ms batch flush
        }
      }
    } catch (_) {}
  });
})();
