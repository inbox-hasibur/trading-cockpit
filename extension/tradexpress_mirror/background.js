/**
 * Humming Bird — TradeXpress Passive Mirror (Background Service Worker)
 *
 * MV3 Service Worker forwarding passively sniffed TradeXpress DOM snapshots
 * and network tap events exclusively to local Humming Bird Cockpit (127.0.0.1:8000).
 *
 * ZERO-BAN & STRICT LOCALHOST MANDATE:
 * Absolutely NO requests to non-localhost URLs.
 */

const LOCAL_INGEST_URL = 'http://127.0.0.1:8000/api/tradexpress/passive-ingest';
const LOCAL_NET_TAP_URL = 'http://127.0.0.1:8000/api/tradexpress/passive-net-tap';

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    mirrorEnabled: true,
    connected: false,
    lastSyncAt: null,
    rowsSent: 0,
    activeTab: 'none',
    dseStatus: 'UNKNOWN',
    lastError: null,
    wsInCount: 0,
    wsOutCount: 0,
    xhrCount: 0,
    netTapEventsSent: 0,
  });
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message && message.type === 'PASSIVE_SNAPSHOT') {
    const payload = message.payload || {};

    fetch(LOCAL_INGEST_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Hummingbird-Source': 'EDGE_EXTENSION_PASSIVE',
      },
      body: JSON.stringify(payload),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Cockpit returned HTTP ${response.status}`);
        }
        const data = await response.json();
        const telemetry = {
          connected: true,
          lastSyncAt: new Date().toLocaleTimeString(),
          rowsSent: (payload.market_watch_rows || []).length,
          activeTab: payload.tab || 'market_watch',
          dseStatus: payload.dse_status || 'UNKNOWN',
          lastError: null,
        };
        chrome.storage.local.set(telemetry);
        sendResponse({ success: true, data });
      })
      .catch((err) => {
        const errorMsg = err && err.message ? err.message : String(err);
        chrome.storage.local.set({
          connected: false,
          lastError: errorMsg,
        });
        sendResponse({ success: false, error: errorMsg });
      });

    return true; // Keep message channel open for async response
  }

  if (message && message.type === 'PASSIVE_NET_BATCH') {
    const events = message.events || [];
    if (events.length === 0) {
      sendResponse({ success: true, count: 0 });
      return;
    }

    fetch(LOCAL_NET_TAP_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Hummingbird-Source': 'EDGE_EXTENSION_PASSIVE',
      },
      body: JSON.stringify({ events }),
    })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Cockpit returned HTTP ${response.status}`);
        }
        const data = await response.json();
        chrome.storage.local.get(
          ['wsInCount', 'wsOutCount', 'xhrCount', 'netTapEventsSent'],
          (current) => {
            let wsIn = current.wsInCount || 0;
            let wsOut = current.wsOutCount || 0;
            let xhr = current.xhrCount || 0;
            events.forEach((e) => {
              const t = (e.type || '').toLowerCase();
              if (t === 'ws_in') wsIn++;
              else if (t === 'ws_out') wsOut++;
              else if (t === 'xhr' || t === 'fetch') xhr++;
            });
            chrome.storage.local.set({
              wsInCount: wsIn,
              wsOutCount: wsOut,
              xhrCount: xhr,
              netTapEventsSent: (current.netTapEventsSent || 0) + events.length,
            });
          }
        );
        sendResponse({ success: true, data });
      })
      .catch((err) => {
        sendResponse({ success: false, error: String(err) });
      });

    return true;
  }
});
