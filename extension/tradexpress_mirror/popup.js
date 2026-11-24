/**
 * Humming Bird — TradeXpress Passive Mirror Popup Logic
 */

document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.getElementById('mirror-toggle');
  const dot = document.getElementById('status-dot');
  const statusText = document.getElementById('status-text');
  const activeTabEl = document.getElementById('active-tab');
  const dseStatusEl = document.getElementById('dse-status');
  const rowsSentEl = document.getElementById('rows-sent');
  const wsInEl = document.getElementById('ws-in');
  const wsOutEl = document.getElementById('ws-out');
  const xhrCountEl = document.getElementById('xhr-count');
  const lastSyncEl = document.getElementById('last-sync');

  function render(state) {
    if (toggle) {
      toggle.checked = state.mirrorEnabled !== false;
    }

    if (activeTabEl) activeTabEl.textContent = state.activeTab || '—';
    if (dseStatusEl) dseStatusEl.textContent = state.dseStatus || '—';

    const rows = state.domRowsSent != null ? state.domRowsSent : (state.rowsSent != null ? state.rowsSent : '0');
    if (rowsSentEl) rowsSentEl.textContent = rows;

    const wsIn = state.wsFramesIn != null ? state.wsFramesIn : (state.wsInCount != null ? state.wsInCount : '0');
    if (wsInEl) wsInEl.textContent = wsIn;

    const wsOut = state.wsFramesOut != null ? state.wsFramesOut : (state.wsOutCount != null ? state.wsOutCount : '0');
    if (wsOutEl) wsOutEl.textContent = wsOut;

    const xhr = state.xhrCaptured != null ? state.xhrCaptured : (state.xhrCount != null ? state.xhrCount : '0');
    if (xhrCountEl) xhrCountEl.textContent = xhr;

    if (lastSyncEl) lastSyncEl.textContent = state.lastSyncAt || '—';

    if (state.mirrorEnabled === false) {
      dot.className = 'dot idle';
      statusText.textContent = 'Paused';
    } else if (state.connected) {
      dot.className = 'dot live';
      statusText.textContent = 'Connected';
    } else if (state.lastError) {
      dot.className = 'dot offline';
      statusText.textContent = 'Offline';
    } else {
      dot.className = 'dot idle';
      statusText.textContent = 'Waiting for itrade';
    }
  }

  const STORAGE_KEYS = [
    'mirrorEnabled',
    'connected',
    'lastSyncAt',
    'domRowsSent',
    'rowsSent',
    'activeTab',
    'dseStatus',
    'lastError',
    'wsFramesIn',
    'wsInCount',
    'wsFramesOut',
    'wsOutCount',
    'xhrCaptured',
    'xhrCount',
    'netTapEventsSent',
  ];

  function fetchStorageAndRender() {
    chrome.storage.local.get(STORAGE_KEYS, (items) => {
      render(items);
    });
  }

  // 1. Initial render from storage
  fetchStorageAndRender();

  // 2. Continuous 1-second refresh timer
  const refreshInterval = setInterval(fetchStorageAndRender, 1000);

  // 3. Fallback active probe against cockpit server on popup open
  // Guarantees popup NEVER falsely shows "Offline / 0" if cockpit server is already live!
  fetch('http://127.0.0.1:8000/api/tradexpress/status')
    .then((res) => {
      if (res.ok) return res.json();
      throw new Error(`HTTP ${res.status}`);
    })
    .then((data) => {
      if (data && (data.bridge_connected || data.status === 'ONLINE')) {
        const netTap = data.net_tap || {};
        const fallbackState = {
          connected: true,
          activeTab: data.active_tab && data.active_tab !== 'none' ? data.active_tab : 'Dhaka Stock Exchange',
          dseStatus: data.dse_status || 'Trading',
          domRowsSent: data.total_ingests_count || 0,
          wsFramesIn: netTap.ws_in_count || 0,
          wsFramesOut: netTap.ws_out_count || 0,
          xhrCaptured: netTap.xhr_count || 0,
          lastSyncAt: data.last_ingest_utc ? new Date(data.last_ingest_utc).toLocaleTimeString() : new Date().toLocaleTimeString(),
          lastError: null,
        };
        chrome.storage.local.set(fallbackState);
        render(fallbackState);
      }
    })
    .catch(() => {
      // Cockpit server might be offline, storage rendering suffices
    });

  // 4. Listen for storage changes
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local') {
      fetchStorageAndRender();
    }
  });

  if (toggle) {
    toggle.addEventListener('change', () => {
      const enabled = toggle.checked;
      chrome.storage.local.set({ mirrorEnabled: enabled });
    });
  }

  window.addEventListener('unload', () => {
    clearInterval(refreshInterval);
  });
});
