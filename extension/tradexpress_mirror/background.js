/**
 * Humming Bird — TradeXpress Passive Mirror (Background Service Worker)
 *
 * MV3 Service Worker forwarding passively sniffed TradeXpress DOM snapshots
 * exclusively to the local Humming Bird Cockpit instance at http://127.0.0.1:8000.
 *
 * ZERO-BAN & STRICT LOCALHOST MANDATE:
 * Absolutely NO requests to non-localhost URLs.
 */

const LOCAL_INGEST_URL = 'http://127.0.0.1:8000/api/tradexpress/passive-ingest';

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({
    mirrorEnabled: true,
    connected: false,
    lastSyncAt: null,
    rowsSent: 0,
    activeTab: 'none',
    dseStatus: 'UNKNOWN',
    lastError: null,
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
});
