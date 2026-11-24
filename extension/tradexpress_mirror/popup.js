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
    if (rowsSentEl) rowsSentEl.textContent = state.rowsSent != null ? state.rowsSent : '0';
    if (wsInEl) wsInEl.textContent = state.wsInCount != null ? state.wsInCount : '0';
    if (wsOutEl) wsOutEl.textContent = state.wsOutCount != null ? state.wsOutCount : '0';
    if (xhrCountEl) xhrCountEl.textContent = state.xhrCount != null ? state.xhrCount : '0';
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
    'rowsSent',
    'activeTab',
    'dseStatus',
    'lastError',
    'wsInCount',
    'wsOutCount',
    'xhrCount',
    'netTapEventsSent',
  ];

  // Load state from local storage
  chrome.storage.local.get(STORAGE_KEYS, (items) => {
    render(items);
  });

  // Listen for storage changes
  chrome.storage.onChanged.addListener((changes, area) => {
    if (area === 'local') {
      chrome.storage.local.get(STORAGE_KEYS, (items) => {
        render(items);
      });
    }
  });

  if (toggle) {
    toggle.addEventListener('change', () => {
      const enabled = toggle.checked;
      chrome.storage.local.set({ mirrorEnabled: enabled });
    });
  }
});
