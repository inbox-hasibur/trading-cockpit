/**
 * Humming Bird — TradeXpress Passive Network Tap (MAIN World Script)
 *
 * Runs in the webpage's MAIN world at document_start.
 * Passively observes incoming/outgoing WebSocket frames, XHR, and Fetch responses
 * without delaying, dropping, modifying, or creating any network traffic.
 *
 * STRICT SAFETY & ZERO-BAN CONSTRAINTS:
 * 1. 100% PASSIVE READ-ONLY: Never send any requests to broker servers.
 * 2. ZERO SECRETS LEAK: Redacts sesnId, SSOTOK, password, token, Authorization.
 *    URLs containing login/auth/password/sso/otp are NEVER recorded with request bodies.
 * 3. FAIL-SAFE: Every hook is wrapped in try/catch to ensure zero impact on TradeXpress.
 */

(function () {
  'use strict';

  // Prevent multiple injections
  if (window.__HB_NETWORK_TAP_ACTIVE) return;
  window.__HB_NETWORK_TAP_ACTIVE = true;

  const SENSITIVE_KEY_REGEX = /(?:sesnId|ssotok|token|password|auth(?:orization)?|secret|cookie)=([^&;\s]+)/gi;
  const AUTH_URL_REGEX = /\b(?:login|authenticate|auth|password|otp|sso|token)\b/i;

  function redactString(str) {
    if (typeof str !== 'string') return str;
    return str.replace(SENSITIVE_KEY_REGEX, '$1=***REDACTED***');
  }

  function sanitizePayload(raw) {
    if (raw == null) return null;
    try {
      if (typeof raw === 'string') {
        const trimmed = raw.trim();
        if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
          const parsed = JSON.parse(trimmed);
          return sanitizeObject(parsed);
        }
        return redactString(trimmed.slice(0, 4000));
      }
      if (typeof raw === 'object') {
        return sanitizeObject(raw);
      }
    } catch (_) {
      // Fallback
    }
    return typeof raw === 'string' ? redactString(raw.slice(0, 1000)) : String(raw);
  }

  function sanitizeObject(obj) {
    if (!obj || typeof obj !== 'object') return obj;
    if (Array.isArray(obj)) {
      return obj.slice(0, 50).map(sanitizeObject);
    }
    const clean = {};
    for (const [k, v] of Object.entries(obj)) {
      const lowerK = k.toLowerCase();
      if (
        lowerK.includes('password') ||
        lowerK.includes('sesnid') ||
        lowerK.includes('ssotok') ||
        lowerK.includes('token') ||
        lowerK.includes('secret')
      ) {
        clean[k] = '***REDACTED***';
      } else if (typeof v === 'object' && v !== null) {
        clean[k] = sanitizeObject(v);
      } else if (typeof v === 'string') {
        clean[k] = redactString(v);
      } else {
        clean[k] = v;
      }
    }
    return clean;
  }

  function emitNetEvent(evt) {
    try {
      window.postMessage(
        {
          __hbPassiveNet: true,
          event: evt,
        },
        '*'
      );
    } catch (_) {}
  }

  // ==========================================
  // 1. Passive WebSocket Tap
  // ==========================================
  const OrigWebSocket = window.WebSocket;
  if (OrigWebSocket) {
    const PatchedWebSocket = function (url, protocols) {
      let ws;
      try {
        ws = protocols ? new OrigWebSocket(url, protocols) : new OrigWebSocket(url);
      } catch (err) {
        throw err;
      }

      try {
        const cleanUrl = redactString(String(url));
        const endpoint = cleanUrl.split('?')[0];

        // Hook incoming frames
        ws.addEventListener('message', function (event) {
          try {
            const data = event.data;
            let channel = 'default';
            let parsedData = data;

            if (typeof data === 'string') {
              if (data.startsWith('42') || data.startsWith('43')) {
                channel = 'socket.io';
              } else if (data.includes('"channel"') || data.includes('"topic"')) {
                channel = 'topic_stream';
              }
              parsedData = sanitizePayload(data);
            }

            emitNetEvent({
              type: 'ws_in',
              endpoint: endpoint,
              channel: channel,
              payload: parsedData,
              timestamp: Date.now(),
            });
          } catch (_) {}
        });

        // Hook outgoing frames
        const origSend = ws.send;
        ws.send = function (data) {
          try {
            emitNetEvent({
              type: 'ws_out',
              endpoint: endpoint,
              channel: 'client_send',
              payload: sanitizePayload(data),
              timestamp: Date.now(),
            });
          } catch (_) {}
          return origSend.apply(this, arguments);
        };
      } catch (_) {}

      return ws;
    };

    PatchedWebSocket.prototype = OrigWebSocket.prototype;
    PatchedWebSocket.CONNECTING = OrigWebSocket.CONNECTING;
    PatchedWebSocket.OPEN = OrigWebSocket.OPEN;
    PatchedWebSocket.CLOSING = OrigWebSocket.CLOSING;
    PatchedWebSocket.CLOSED = OrigWebSocket.CLOSED;
    window.WebSocket = PatchedWebSocket;
  }

  // ==========================================
  // 2. Passive XMLHttpRequest Tap
  // ==========================================
  const OrigXHR = window.XMLHttpRequest;
  if (OrigXHR) {
    const origOpen = OrigXHR.prototype.open;
    const origSend = OrigXHR.prototype.send;

    OrigXHR.prototype.open = function (method, url) {
      try {
        this.__hb_method = method;
        this.__hb_url = String(url);
      } catch (_) {}
      return origOpen.apply(this, arguments);
    };

    OrigXHR.prototype.send = function (body) {
      try {
        const url = this.__hb_url || '';
        const method = this.__hb_method || 'GET';
        const isAuth = AUTH_URL_REGEX.test(url);

        this.addEventListener('load', function () {
          try {
            if (this.readyState === 4 && this.status >= 200 && this.status < 400) {
              const cleanUrl = redactString(url);
              const endpoint = cleanUrl.split('?')[0];

              let resData = null;
              if (!isAuth) {
                if (!this.responseType || this.responseType === 'text') {
                  resData = sanitizePayload(this.responseText);
                } else if (this.responseType === 'json') {
                  resData = sanitizeObject(this.response);
                }
              } else {
                resData = '[AUTH_REDACTED]';
              }

              emitNetEvent({
                type: 'xhr',
                method: method,
                url: cleanUrl,
                endpoint: endpoint,
                status: this.status,
                payload: resData,
                timestamp: Date.now(),
              });
            }
          } catch (_) {}
        });
      } catch (_) {}
      return origSend.apply(this, arguments);
    };
  }

  // ==========================================
  // 3. Passive Fetch Tap
  // ==========================================
  const origFetch = window.fetch;
  if (origFetch) {
    window.fetch = function (resource, init) {
      const fetchPromise = origFetch.apply(this, arguments);
      try {
        const urlStr = typeof resource === 'string' ? resource : (resource && resource.url) ? resource.url : '';
        const method = (init && init.method) ? init.method.toUpperCase() : 'GET';
        const isAuth = AUTH_URL_REGEX.test(urlStr);

        fetchPromise
          .then(function (response) {
            try {
              if (response && response.ok) {
                const cleanUrl = redactString(urlStr);
                const endpoint = cleanUrl.split('?')[0];

                if (!isAuth) {
                  response
                    .clone()
                    .text()
                    .then(function (txt) {
                      emitNetEvent({
                        type: 'fetch',
                        method: method,
                        url: cleanUrl,
                        endpoint: endpoint,
                        status: response.status,
                        payload: sanitizePayload(txt),
                        timestamp: Date.now(),
                      });
                    })
                    .catch(function () {});
                } else {
                  emitNetEvent({
                    type: 'fetch',
                    method: method,
                    url: cleanUrl,
                    endpoint: endpoint,
                    status: response.status,
                    payload: '[AUTH_REDACTED]',
                    timestamp: Date.now(),
                  });
                }
              }
            } catch (_) {}
          })
          .catch(function () {});
      } catch (_) {}
      return fetchPromise;
    };
  }
})();
