"use strict";

// ==========================================================================
// Project Humming Bird · Hermes Copilot UI & Settings/Auth Controller
// Resizable sidebar, conversations, AI model switcher, diffs, auth, and API keys.
// ==========================================================================

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
      top.append(element("strong", "", s.title || s.name));
      top.append(element("span", "skill-rev", `v${s.version || "1.0.0"}${s.revision_count ? ` · ${s.revision_count} patches` : ""}`));
      const tags = element("div", "skill-tags");
      (s.tags || []).forEach((t) => tags.append(element("span", "skill-tag", t)));
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

  // Also trigger full state load in background
  loadHermesOSState();
}

async function loadHermesOSState() {
  try {
    const data = await api("/api/hermes/bridge/state");

    // 1. Active Model Display
    if (data.model) {
      setText("hermes-active-model-name", data.model);
      const rawProv = (data.provider || "").toLowerCase();
      const modelLower = (data.model || "").toLowerCase();
      let prefixLabel = "GOOGLE ·";
      let provDesc = "Direct Google Gemini API";
      if (rawProv === "openrouter" || modelLower.includes("/") || (!modelLower.includes("gemini") && rawProv !== "gemini" && rawProv !== "google")) {
        prefixLabel = "OPENROUTER ·";
        provDesc = "OpenRouter Gateway API";
      } else {
        prefixLabel = "GOOGLE ·";
        provDesc = "Direct Google Gemini API";
      }
      setText("provider-prefix-label", prefixLabel);
      const modelTrigger = $("hermes-model-trigger") || $("hermes-model-display");
      if (modelTrigger) {
        modelTrigger.title = `Active AI Brain: ${data.model} (${provDesc}) — Click to switch model`;
      }
    }

    // 2. Procedural Skills
    const skillsList = $("skills-list");
    const skillsBadge = $("skills-badge");
    const skills = data.skills || [];
    if (skillsBadge) skillsBadge.textContent = skills.length;

    if (skillsList) {
      if (skills.length) {
        skillsList.innerHTML = skills.map((s) => `
          <div class="skill-card">
            <div class="skill-card-top">
              <strong>${escapeHtml(s.title || s.name)}</strong>
              <span class="skill-rev">v${escapeHtml(s.version || "1.0.0")}</span>
              ${s.is_auto_learned ? '<span class="skill-badge-autolearned">LEARNED</span>' : `<span class="skill-tag">${escapeHtml(s.source || "plugin")}</span>`}
            </div>
            <div class="muted small">${escapeHtml(s.description || "")}</div>
            <div class="skill-tags">
              ${(s.tags || []).map((t) => `<span class="skill-tag">#${escapeHtml(t)}</span>`).join("")}
            </div>
          </div>
        `).join("");
      } else {
        skillsList.innerHTML = '<div class="muted small">No procedural skills loaded.</div>';
      }
    }

    // 3. Memory & Profile Previews
    const userPreview = $("user-md-preview");
    if (userPreview) {
      userPreview.textContent = data.user_md || "No operator directives in USER.md.";
    }
    const memPreview = $("memory-md-preview");
    if (memPreview) {
      memPreview.textContent = data.memory_md || "No working market memory in MEMORY.md.";
    }

    // 4. Autonomous Cron Jobs
    renderHermesCronJobs(data.crons || []);

    // 5. Read-Only Brain Card in Settings
    renderHermesBrainCard(data);
  } catch (err) {
    console.debug("Hermes OS state notice:", err);
  }
}

function renderHermesBrainCard(data) {
  if (!data) return;
  const primModel = data.primary_model || data.model || "gemini-3.1-flash-lite";
  const primProvider = data.primary_provider || data.provider || "gemini";
  const profileName = data.profile || "hummingbird";

  setText("brain-primary-model", primModel);
  setText("brain-primary-provider", primProvider);
  setText("brain-profile-tag", profileName);

  // Render Fallback list
  const fallbacksList = $("brain-fallbacks-list");
  if (fallbacksList) {
    const fbs = data.fallbacks || [];
    if (!fbs.length) {
      fallbacksList.innerHTML = `
        <div class="muted small" id="brain-fallbacks-empty" style="padding: 10px 12px; background: rgba(255, 255, 255, 0.02); border: 1px dashed var(--border-color); border-radius: 6px;">
          No fallback providers configured in <code>config.yaml</code>. Run <code>hermes fallback add</code> to append failover models.
        </div>
      `;
    } else {
      fallbacksList.innerHTML = fbs.map((fb, idx) => `
        <div class="chain-step-card" style="margin-bottom: 6px;">
          <span class="step-num">FB ${idx + 1}</span>
          <div class="step-desc">
            <strong>${escapeHtml(fb.model || "unknown")}</strong>
            <span>Provider: ${escapeHtml(fb.provider || "custom")}</span>
          </div>
          <span class="chain-status-badge standby">STANDBY</span>
        </div>
      `).join("");
    }
  }

  // Last turn execution info
  const lastTurn = data.last_turn || {};
  setText("brain-last-turn-provider", lastTurn.provider || primProvider);
  setText("brain-last-turn-model", `(${lastTurn.model || primModel})`);
  if (lastTurn.timestamp) {
    try {
      const dt = new Date(lastTurn.timestamp);
      setText("brain-last-turn-time", dt.toLocaleTimeString());
    } catch {
      setText("brain-last-turn-time", "Recent");
    }
  } else {
    setText("brain-last-turn-time", "Ready");
  }
}

function renderHermesCronJobs(crons) {
  const cronsList = $("crons-list");
  if (!cronsList) return;
  if (!crons || !crons.length) {
    cronsList.innerHTML = '<div class="cron-empty-hint">No cron jobs scheduled in Hermes.</div>';
    return;
  }
  cronsList.innerHTML = crons.map((j) => {
    const isPaused = j.state === "paused" || j.enabled === false;
    return `
      <div class="cron-card ${isPaused ? "cron-paused" : ""}" data-cron-id="${escapeHtml(j.id)}">
        <div class="cron-card-header">
          <span class="cron-name"><strong>${escapeHtml(j.name || j.id)}</strong> <span class="muted small">(${escapeHtml(j.id)})</span></span>
          <span class="cron-state-badge ${isPaused ? "paused" : "scheduled"}">${isPaused ? "PAUSED" : "ACTIVE"}</span>
        </div>
        <div class="cron-schedule">⏰ ${escapeHtml(j.schedule_expr || "")} (${escapeHtml(j.timezone || "Asia/Dhaka")})</div>
        ${j.next_run ? `<div class="muted small">Next: ${escapeHtml(j.next_run)}</div>` : ""}
        ${j.last_run ? `<div class="muted small">Last: ${escapeHtml(j.last_run)} [${escapeHtml(j.last_status || "ok")}]</div>` : ""}
        <div class="cron-actions">
          ${isPaused
        ? `<button type="button" class="cron-btn resume" onclick="window.resumeHermesCron('${escapeHtml(j.id)}')">▶ Resume</button>`
        : `<button type="button" class="cron-btn pause" onclick="window.pauseHermesCron('${escapeHtml(j.id)}')">⏸ Pause</button>`
      }
          <button type="button" class="cron-btn delete" onclick="window.deleteHermesCron('${escapeHtml(j.id)}')">🗑 Delete</button>
        </div>
      </div>
    `;
  }).join("");
}

window.pauseHermesCron = async function (jobId) {
  if (!jobId) return;
  try {
    await api(`/api/hermes/bridge/cron/${encodeURIComponent(jobId)}/pause`, { method: "POST" });
    notify(`Cron job ${jobId} paused in Hermes.`);
    await loadHermesOSState();
  } catch (err) {
    notify(`Failed to pause cron: ${err.message}`, true);
  }
};

window.resumeHermesCron = async function (jobId) {
  if (!jobId) return;
  try {
    await api(`/api/hermes/bridge/cron/${encodeURIComponent(jobId)}/resume`, { method: "POST" });
    notify(`Cron job ${jobId} resumed in Hermes.`);
    await loadHermesOSState();
  } catch (err) {
    notify(`Failed to resume cron: ${err.message}`, true);
  }
};

window.deleteHermesCron = async function (jobId) {
  if (!jobId || !confirm(`Delete cron job ${jobId} from Hermes?`)) return;
  try {
    await api(`/api/hermes/bridge/cron/${encodeURIComponent(jobId)}`, { method: "DELETE" });
    notify(`Cron job ${jobId} deleted from Hermes.`);
    await loadHermesOSState();
  } catch (err) {
    notify(`Failed to delete cron: ${err.message}`, true);
  }
};

window.toggleCron = function (jobId) {
  return window.pauseHermesCron(jobId);
};
window.deleteCron = window.deleteHermesCron;

function formatChatMarkdown(text) {
  if (!text) return "";
  let safe = escapeHtml(text);
  // Code spans `code`
  safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Bold **bold**
  safe = safe.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

  // Bullet items (* item, - item, • item) and Headings (###, ##, #)
  const lines = safe.split("\n");
  const formatted = [];
  let inList = false;
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith("* ") || trimmed.startsWith("- ") || trimmed.startsWith("• ")) {
      if (!inList) {
        formatted.push('<ul class="chat-bullet-list">');
        inList = true;
      }
      formatted.push(`<li>${trimmed.slice(2).trim()}</li>`);
    } else {
      if (inList) {
        formatted.push("</ul>");
        inList = false;
      }
      if (/^#{1,3}\s+/.test(trimmed)) {
        const headingText = trimmed.replace(/^#{1,3}\s+/, "");
        formatted.push(`<div class="chat-h">${headingText}</div>`);
      } else {
        formatted.push(line);
      }
    }
  }
  if (inList) formatted.push("</ul>");
  return formatted.join("<br>")
    .replace(/<br><ul/g, "<ul")
    .replace(/<\/ul><br>/g, "</ul>")
    .replace(/<br><div class="chat-h">/g, '<div class="chat-h">')
    .replace(/<\/div><br>/g, "</div>");
}

function syncQuickPromptsPlacement() {
  const prompts = $("chat-quick-prompts");
  const welcomeSlot = $("welcome-chips-slot");
  const bottomSlot = $("bottom-chips-slot");
  if (!prompts || !welcomeSlot || !bottomSlot) return;

  const chatContainer = $("chat-messages");
  const nonWelcomeCount = chatContainer ? chatContainer.querySelectorAll(".chat-message:not(.welcome-message)").length : 0;

  if (nonWelcomeCount > 0) {
    if (prompts.parentElement !== bottomSlot) {
      bottomSlot.appendChild(prompts);
    }
  } else {
    if (prompts.parentElement !== welcomeSlot) {
      welcomeSlot.appendChild(prompts);
    }
  }
}

function addMessage(role, content, provider = null) {
  const article = element("article", `chat-message ${role}`);
  const author = element("div", "message-author");
  if (role === "assistant") author.append(element("span", "assistant-avatar", "✦"));
  author.append(document.createTextNode(role === "user" ? "YOU" : "HERMES"));
  if (provider) {
    author.append(element("span", "muted", `· ${provider.toUpperCase()}`));
  }
  const body = element("div", "message-body");
  body.innerHTML = formatChatMarkdown(content);
  article.append(author, body);
  $("chat-messages").append(article);
  $("chat-messages").scrollTop = $("chat-messages").scrollHeight;
  syncQuickPromptsPlacement();
  return article;
}

// --------------------------------------------------------------------------
// Order Preview Card & Execution Lifecycle (Requirement 10)
// --------------------------------------------------------------------------

function isOrderPreview(data, toolName = "") {
  if (!data || typeof data !== "object") return false;
  if (data.preview_token) return true;
  if (data.order_preview) return true;
  if (data.dry_run === true && (data.status === "VALIDATED" || data.status === "PREVIEW")) return true;
  if (data.requires_confirmation === true) return true;
  if (toolName === "hb_place_order" && data.dry_run !== false && (data.symbol || data.order_preview)) return true;
  return false;
}

function renderOrderPreviewCard(previewData, container = null) {
  const preview = previewData.order_preview ? { ...previewData.order_preview, ...previewData } : previewData;
  const symbol = String(preview.symbol || "").toUpperCase();
  const side = String(preview.side || "BUY").toUpperCase();
  const qty = Number(preview.quantity || preview.qty || 1);
  const price = Number(preview.price || 0);
  const feePct = Number(preview.commission_pct || 0.5);
  const fee = preview.estimated_fee !== undefined ? Number(preview.estimated_fee) : Number((qty * price * feePct / 100).toFixed(2));
  const net = preview.estimated_net !== undefined ? Number(preview.estimated_net) : (side === "BUY" ? Number((qty * price + fee).toFixed(2)) : Number((qty * price - fee).toFixed(2)));
  const mode = preview.trading_mode || (state.snapshot?.app?.trading_mode) || "LIVE_HOURS";
  const modeLabel = mode === "TEST_OFFHOURS" ? "Test Mode" : "Live Hours";
  const pid = String(preview.portfolio_id || (mode === "TEST_OFFHOURS" ? (state.snapshot?.portfolio?.test_portfolio_id || "164580") : "164580"));
  const pName = preview.portfolio_name || (pid === "164580" ? "Humming Bird" : "Test Portfolio");
  const token = preview.preview_token || `prev_${Math.random().toString(36).substring(2, 10)}`;

  // Cap usage
  const caps = preview.cap_usage || {};
  let capSummary = caps.summary || "";
  if (!capSummary) {
    if (caps.orders_ratio) {
      capSummary = `Orders: ${caps.orders_ratio} · Daily Budget: ৳${numberFormat.format(caps.daily_budget_after || net)}`;
    } else {
      capSummary = "Limits & daily budget checked";
    }
  }
  const dailyPct = caps.daily_budget_pct !== undefined ? Number(caps.daily_budget_pct) : null;

  // Create card element
  const card = document.createElement("div");
  card.className = "order-preview-card";
  card.id = `order-preview-${token}`;
  card.dataset.previewToken = token;
  card.dataset.symbol = symbol;
  card.dataset.side = side;
  card.dataset.qty = String(qty);
  card.dataset.price = String(price);
  card.dataset.portfolioId = pid;

  card.innerHTML = `
    <div class="order-card-header">
      <div class="order-card-headline">
        <span class="badge ${side.toLowerCase()} order-side-badge">${side}</span>
        <strong class="order-card-symbol">${escapeHtml(symbol)}</strong>
        <span class="order-card-qty">${qty} share${qty > 1 ? "s" : ""}</span>
      </div>
      <div class="order-card-meta">
        <span class="order-pill-mode">${escapeHtml(modeLabel)}</span>
        <span class="order-pill-port">${escapeHtml(pName)} #${escapeHtml(pid)}</span>
      </div>
    </div>

    <div class="order-specs-grid">
      <div class="order-spec-cell">
        <span class="spec-label">PRICE</span>
        <span class="spec-value">৳${numberFormat.format(price)}</span>
      </div>
      <div class="order-spec-cell">
        <span class="spec-label">FEE (0.5%)</span>
        <span class="spec-value">৳${numberFormat.format(fee)}</span>
      </div>
      <div class="order-spec-cell">
        <span class="spec-label">EST. NET</span>
        <span class="spec-value highlight">৳${numberFormat.format(net)}</span>
      </div>
    </div>

    <div class="order-cap-box">
      <div class="cap-box-header">
        <span class="cap-box-title">🛡️ Cap Usage</span>
        <span class="cap-box-summary">${escapeHtml(capSummary)}</span>
      </div>
      ${dailyPct !== null ? `
        <div class="cap-bar-wrap" title="Daily Budget Utilization: ${dailyPct}%">
          <div class="cap-bar-fill ${dailyPct > 90 ? 'critical' : (dailyPct > 70 ? 'warn' : '')}" style="width: ${Math.min(dailyPct, 100)}%;"></div>
        </div>
      ` : ""}
    </div>

    <div class="order-actions-slot">
      <div class="order-buttons-row">
        <button type="button" class="button primary order-btn-confirm" id="btn-confirm-${token}">
          Confirm Order
        </button>
        <button type="button" class="button secondary order-btn-cancel" id="btn-cancel-${token}">
          Cancel
        </button>
      </div>
      <div class="order-note-sub">Direct virtual submission · No parameters to type</div>
    </div>
  `;

  // Attach button handlers
  const confirmBtn = card.querySelector(".order-btn-confirm");
  const cancelBtn = card.querySelector(".order-btn-cancel");
  const actionsSlot = card.querySelector(".order-actions-slot");

  cancelBtn.addEventListener("click", () => {
    confirmBtn.disabled = true;
    cancelBtn.disabled = true;
    card.classList.add("is-cancelled");
    actionsSlot.innerHTML = `
      <div class="order-status-banner cancelled">
        <span class="status-icon">✕</span>
        <span>Order preview cancelled by operator. No trades submitted.</span>
      </div>
    `;
  });

  confirmBtn.addEventListener("click", async () => {
    confirmBtn.disabled = true;
    cancelBtn.disabled = true;
    confirmBtn.innerHTML = `<span class="spinner-inline"></span> Submitting to StockNow…`;

    try {
      const orderPayload = {
        symbol: symbol,
        side: side,
        quantity: qty,
        price: price > 0 ? price : undefined,
        portfolio_id: pid,
        preview_token: token,
        dry_run: false,
        operator_confirmed: true,
        idempotency_key: `confirm-${token}-${Date.now()}`,
      };

      const result = await api("/k/order", {
        method: "POST",
        body: orderPayload,
      });

      // Successful execution: Transition to verified receipt state
      card.classList.add("is-receipt");
      const receipt = result.stocknow_receipt || {};
      const trade = result.trade || {};
      const receiptId = receipt.order_id || receipt.receipt_id || trade.trade_key || `REC-${Date.now().toString(36).toUpperCase()}`;
      const receiptTag = (receipt.execution_mode === "DEMO_PAPER" || result.source === "DEMO_PAPER") ? "PAPER FILL" : "STOCKNOW RECEIPT";
      const fillPrice = receipt.price || trade.price || price;
      const netCash = Math.abs(trade.net_cash_change || net);

      actionsSlot.innerHTML = `
        <div class="order-receipt-state">
          <div class="receipt-header">
            <span class="receipt-icon">✓</span>
            <span class="receipt-title">Order Executed Successfully</span>
            <span class="receipt-tag">${receiptTag}</span>
          </div>
          <div class="receipt-grid">
            <div class="receipt-item">
              <span class="item-label">Receipt ID</span>
              <strong class="item-val">#${escapeHtml(receiptId)}</strong>
            </div>
            <div class="receipt-item">
              <span class="item-label">Fill</span>
              <span class="item-val">${side} ${qty} ${symbol} @ ৳${numberFormat.format(fillPrice)}</span>
            </div>
            <div class="receipt-item">
              <span class="item-label">Net BDT</span>
              <span class="item-val">৳${numberFormat.format(netCash)}</span>
            </div>
            <div class="receipt-item">
              <span class="item-label">Portfolio</span>
              <span class="item-val">${escapeHtml(pName)} #${escapeHtml(pid)}</span>
            </div>
          </div>
          <div class="receipt-status-sub">
            <span class="receipt-dot green"></span> Status: ${escapeHtml(receipt.status || "ACKNOWLEDGED")} · Local ledger synchronized · 0.00 drift
          </div>
        </div>
      `;

      // Trigger Cockpit refresh so active holdings, ledger & topbar update
      if (typeof refresh === "function") {
        await refresh(true);
      }

    } catch (err) {
      // Execution failed: Render red error banner with exact required text
      card.classList.add("is-failed");
      let reason = err.message || "Execution rejected by broker";
      try {
        const parsed = JSON.parse(reason);
        reason = parsed.detail?.detail || parsed.detail?.error || parsed.detail || parsed.message || reason;
      } catch {}

      actionsSlot.innerHTML = `
        <div class="order-failed-state">
          <div class="order-failed-title">
            <span class="alert-icon">⚠️</span> live submission failed: ${escapeHtml(reason)}
          </div>
          <div class="order-failed-sub">
            with no ledger change · State restored to pre-order checkpoint.
          </div>
        </div>
      `;
    }
  });

  // Append to target container or chat
  if (!container) {
    const chatContainer = $("chat-messages");
    if (chatContainer) {
      let lastMsg = chatContainer.querySelector(".chat-message:last-child .message-body");
      container = lastMsg || chatContainer;
    }
  }

  if (container) {
    container.appendChild(card);
    const chatMsgBox = $("chat-messages");
    if (chatMsgBox) chatMsgBox.scrollTop = chatMsgBox.scrollHeight;
  }

  return card;
}

window.isOrderPreview = isOrderPreview;
window.renderOrderPreviewCard = renderOrderPreviewCard;

async function sendChat(message) {
  message = message.trim();
  if (!message || message.length > 4000 || state.chatBusy) return;

  // Direct chat shortcut: /order or /preview
  if (/^\/(?:order|preview)\b/i.test(message)) {
    addMessage("user", message);
    state.history.push({ role: "user", content: message });
    $("chat-input").value = "";
    state.chatBusy = true;
    updateControls();

    const article = element("article", "chat-message assistant");
    const author = element("div", "message-author");
    author.append(element("span", "assistant-avatar", "✦"));
    author.append(document.createTextNode("HERMES"));
    const modelName = $("hermes-active-model-name")?.textContent || "gemini-3.1-flash-lite";
    author.append(element("span", "muted", ` · ${modelName}`));

    const body = element("div", "message-body");
    const toolsContainer = element("div", "tool-cards-container");
    const textContent = element("div", "message-text-content");
    body.append(toolsContainer, textContent);
    article.append(author, body);
    $("chat-messages").append(article);
    $("chat-messages").scrollTop = $("chat-messages").scrollHeight;
    syncQuickPromptsPlacement();

    try {
      const match = message.match(/^\/(?:order|preview)\s+(buy|sell)\s+(\d+)\s+([A-Za-z0-9_-]+)(?:\s+([\d.]+))?/i);
      if (!match) {
        textContent.innerHTML = `<div class="response-warning">Usage: <code>/preview &lt;BUY|SELL&gt; &lt;qty&gt; &lt;symbol&gt; [price]</code> (e.g. <code>/preview buy 10 BANKASIA</code>)</div>`;
      } else {
        const side = match[1].toUpperCase();
        const qty = parseInt(match[2], 10);
        const symbol = match[3].toUpperCase();
        const price = match[4] ? parseFloat(match[4]) : undefined;
        textContent.innerHTML = `<em>Validating order preview for ${side} ${qty} ${symbol}…</em>`;

        const previewRes = await api("/k/order", {
          method: "POST",
          body: {
            symbol,
            side,
            quantity: qty,
            price,
            dry_run: true,
            idempotency_key: `preview-${symbol}-${side}-${qty}-${Date.now()}`,
          },
        });

        textContent.innerHTML = `Order preview validated. Review details and confirm below to execute:`;
        renderOrderPreviewCard(previewRes, toolsContainer);
      }
    } catch (err) {
      textContent.innerHTML = `<div class="response-warning">Order preview rejected: ${escapeHtml(err.message || String(err))}</div>`;
    } finally {
      state.chatBusy = false;
      updateControls();
    }
    return;
  }

  addMessage("user", message);
  state.history.push({ role: "user", content: message });
  $("chat-input").value = "";
  state.chatBusy = true;
  updateControls();

  // Create streaming assistant message article
  const article = element("article", "chat-message assistant");
  const author = element("div", "message-author");
  author.append(element("span", "assistant-avatar", "✦"));
  author.append(document.createTextNode("HERMES"));
  const modelName = $("hermes-active-model-name")?.textContent || "gemini-3.1-flash-lite";
  author.append(element("span", "muted", ` · ${modelName}`));

  const body = element("div", "message-body");
  const toolsContainer = element("div", "tool-cards-container");
  const textContent = element("div", "message-text-content");
  const thinking = element("span", "thinking", "Hermes is thinking…");

  body.append(toolsContainer, textContent, thinking);
  article.append(author, body);
  $("chat-messages").append(article);
  $("chat-messages").scrollTop = $("chat-messages").scrollHeight;
  syncQuickPromptsPlacement();

  let streamedText = "";
  let toolsUsedCount = 0;
  const activeToolCards = {};

  try {
    const resp = await fetch("/api/hermes/bridge/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        session_id: state.activeConversationId || undefined,
      }),
    });

    if (!resp.ok) {
      throw new Error(`Hermes bridge returned HTTP ${resp.status}`);
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        for (const rawLine of block.split("\n")) {
          const line = rawLine.trim();
          if (!line.startsWith("data: ")) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const evt = JSON.parse(jsonStr);

            if (evt.type === "tool_use") {
              if (thinking.parentElement) thinking.remove();
              toolsUsedCount++;
              const toolId = evt.id || `tool_${Date.now()}_${toolsUsedCount}`;
              const card = document.createElement("div");
              card.className = "tool-call-card running";
              card.id = `tool-card-${toolId}`;
              card.dataset.toolName = evt.name || "";

              const argsStr = typeof evt.input === "object" ? JSON.stringify(evt.input || {}, null, 2) : String(evt.input || "{}");
              card.innerHTML = `
                <div class="tool-card-header" onclick="this.parentElement.classList.toggle('collapsed')">
                  <span class="tool-card-title">⚡ Tool: <strong>${escapeHtml(evt.name)}</strong></span>
                  <span class="tool-status running">Running…</span>
                </div>
                <div class="tool-card-body">
                  <div class="tool-section-label">INPUT ARGUMENTS</div>
                  <pre class="tool-pre tool-args">${escapeHtml(argsStr)}</pre>
                  <div class="tool-result-section" style="display:none;">
                    <div class="tool-section-label">OUTPUT RESULT</div>
                    <pre class="tool-pre tool-output"></pre>
                  </div>
                </div>
              `;
              toolsContainer.appendChild(card);
              activeToolCards[toolId] = card;
              $("chat-messages").scrollTop = $("chat-messages").scrollHeight;

            } else if (evt.type === "tool_result") {
              const toolId = evt.id;
              const card = activeToolCards[toolId] || toolsContainer.querySelector(".tool-call-card.running");
              if (card) {
                card.classList.remove("running");
                card.classList.add(evt.is_error ? "error" : "completed");
                const statusSpan = card.querySelector(".tool-status");
                if (statusSpan) {
                  statusSpan.className = `tool-status ${evt.is_error ? "error" : "completed"}`;
                  statusSpan.textContent = evt.is_error ? "Failed" : "Done";
                }
                const resSec = card.querySelector(".tool-result-section");
                const resPre = card.querySelector(".tool-output");
                let parsedOutput = null;
                if (resSec && resPre) {
                  resSec.style.display = "block";
                  let outText = String(evt.output || "");
                  try {
                    parsedOutput = typeof evt.output === "object" ? evt.output : JSON.parse(outText);
                    outText = JSON.stringify(parsedOutput, null, 2);
                  } catch { }
                  resPre.textContent = outText;
                }
                const toolName = card.dataset.toolName || "";
                if (parsedOutput && isOrderPreview(parsedOutput, toolName)) {
                  card.classList.add("collapsed");
                  renderOrderPreviewCard(parsedOutput, toolsContainer);
                }
              }
              $("chat-messages").scrollTop = $("chat-messages").scrollHeight;

            } else if (evt.type === "text") {
              if (thinking.parentElement) thinking.remove();
              streamedText += evt.text;
              textContent.innerHTML = formatChatMarkdown(streamedText);
              $("chat-messages").scrollTop = $("chat-messages").scrollHeight;

            } else if (evt.type === "done") {
              if (thinking.parentElement) thinking.remove();
              if (evt.text && !streamedText) {
                streamedText = evt.text;
                textContent.innerHTML = formatChatMarkdown(streamedText);
              }
              if (evt.session_id) {
                state.activeConversationId = evt.session_id;
                localStorage.setItem("humming-bird-active-conv-id", evt.session_id);
              }

            } else if (evt.type === "error") {
              if (thinking.parentElement) thinking.remove();
              textContent.innerHTML += `<div class="response-warning">Hermes Error: ${escapeHtml(evt.error || "Unknown error")}</div>`;
            }
          } catch (err) {
            console.debug("SSE JSON parse notice:", err);
          }
        }
      }
    }

    if (thinking.parentElement) thinking.remove();
    state.history.push({ role: "assistant", content: streamedText.slice(0, 2000) });
    state.history = state.history.slice(-8);

    // If tools executed state mutations, refresh portfolio & skills drawer
    if (toolsUsedCount > 0) {
      await refresh(true);
      loadHermesOSState();
    }
  } catch (err) {
    if (thinking.parentElement) thinking.remove();
    textContent.innerHTML = `<div class="response-warning">Unable to get response from Hermes bridge: ${escapeHtml(err.message)}</div>`;
  } finally {
    state.chatBusy = false;
    updateControls();
    $("chat-input").focus();
  }
}

// --- Hermes IDE Resizable Sidebar, Tabs & Antigravity History ---
function initHermesSidebar() {
  const sidebar = $("hermes-sidebar");
  const resizer = $("hermes-resizer") || $("hermes-resize-handle");
  syncQuickPromptsPlacement();
  const collapseBtn = $("hermes-collapse-btn");
  const openBtn = $("floating-hermes-open");
  const appShell = document.querySelector(".app-shell");

  const applyWidth = (widthPx) => {
    const clamped = Math.min(640, Math.max(280, widthPx));
    document.documentElement.style.setProperty("--hermes-width", `${clamped}px`);
    if (appShell) {
      appShell.style.setProperty("--hermes-width", `${clamped}px`);
    }
    if (sidebar) {
      sidebar.style.removeProperty("width");
      sidebar.style.removeProperty("max-width");
    }
    return clamped;
  };

  // Restore saved width
  const savedWidth = localStorage.getItem("humming-bird-hermes-width");
  if (savedWidth) {
    const parsed = parseInt(savedWidth, 10);
    if (parsed >= 280 && parsed <= 640) {
      applyWidth(parsed);
    }
  } else {
    applyWidth(380);
  }

  // Restore collapsed state
  const isCollapsed = localStorage.getItem("humming-bird-hermes-collapsed") === "true";
  if (isCollapsed && appShell && openBtn) {
    appShell.classList.add("hermes-collapsed");
    openBtn.hidden = false;
  }

  // Drag Resizing with smooth window tracking & cursor stability
  if (resizer && sidebar) {
    let lastWidth = 380;
    const onMouseMove = (e) => {
      // Calculate width from the right edge of viewport to mouse position
      const newWidth = window.innerWidth - e.clientX;
      lastWidth = applyWidth(newWidth);
    };

    const onMouseUp = () => {
      document.body.classList.remove("is-resizing-hermes");
      window.removeEventListener("mousemove", onMouseMove);
      window.removeEventListener("mouseup", onMouseUp);
      window.removeEventListener("blur", onMouseUp);
      localStorage.setItem("humming-bird-hermes-width", lastWidth);
      if (typeof renderMainChart === "function") {
        renderMainChart();
      }
    };

    resizer.addEventListener("mousedown", (e) => {
      e.preventDefault();
      document.body.classList.add("is-resizing-hermes");
      window.addEventListener("mousemove", onMouseMove);
      window.addEventListener("mouseup", onMouseUp);
      window.addEventListener("blur", onMouseUp);
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
    { id: "tab-hermes-skills", paneId: "pane-hermes-skills", onOpen: loadHermesOSState },
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
// state.activeConversationId is initialized inside initHermesSidebar()

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
      await loadHermesOSState();
    }
  } catch (err) {
    notify(`Rollback failed: ${err.message}`, true);
  } finally {
    state.busy = false;
    updateControls();
  }
}

// --- Hermes AI Brain & Runtime Telemetry ---
window.toggleHermesModelPicker = function (e) {
  if (e) {
    if (typeof e.stopPropagation === "function") e.stopPropagation();
    if (typeof e.preventDefault === "function") e.preventDefault();
  }
  const modelDrop = $("model-dropup-menu");
  if (!modelDrop) return;
  const willOpen = modelDrop.hidden;
  modelDrop.hidden = !willOpen;
  const triggerBtn = $("hermes-model-trigger");
  if (triggerBtn) triggerBtn.setAttribute("aria-expanded", String(willOpen));
  if (willOpen) {
    loadHermesModels();
  }
};

window.selectHermesModelItem = function (e, modelId, provider) {
  if (e) {
    if (typeof e.stopPropagation === "function") e.stopPropagation();
    if (typeof e.preventDefault === "function") e.preventDefault();
  }
  const drop = $("model-dropup-menu");
  if (drop) drop.hidden = true;
  const triggerBtn = $("hermes-model-trigger");
  if (triggerBtn) triggerBtn.setAttribute("aria-expanded", "false");
  switchHermesModel(modelId, provider);
};

async function loadHermesModels() {
  const listEl = $("model-dropdown-list");
  if (!listEl) return;
  try {
    const data = await api("/api/hermes/models");
    const models = data.models || [];
    const activeModel = data.active_model || "";
    if (models.length === 0) {
      listEl.innerHTML = '<div class="empty-state-small" style="padding:8px 10px; font-size:11px;">No models available.</div>';
      return;
    }
    listEl.innerHTML = models.map((m) => {
      const isActive = m.id === activeModel || m.name === activeModel;
      const isGoogle = (m.provider || "").toLowerCase().includes("gemini") || (m.provider || "").toLowerCase().includes("google");
      const badgeStyle = isGoogle
        ? "background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3);"
        : "background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);";
      const badgeText = isGoogle ? "Google Direct" : "OpenRouter";
      return `
        <button type="button" class="model-dropup-item ${isActive ? "is-active" : ""}"
                onclick="window.selectHermesModelItem(event, '${escapeHtml(m.id)}', '${escapeHtml(m.provider)}')">
          <div style="display:flex; flex-direction:column; gap:2px; width:100%;">
            <div style="display:flex; align-items:center; justify-content:space-between; width:100%;">
              <span class="model-item-name" style="font-weight:600;">${escapeHtml(m.name)}</span>
              <span style="font-size:9px; padding:1px 5px; border-radius:4px; ${badgeStyle}">${badgeText}</span>
            </div>
            <div style="display:flex; align-items:center; justify-content:space-between; width:100%;">
              <span style="font-size:10px; color:var(--muted, #94a3b8);">${escapeHtml(m.description || m.id)}</span>
              ${isActive ? '<span style="font-size:10px; color:#10b981; font-weight:bold;">✓ Active</span>' : ''}
            </div>
          </div>
        </button>
      `;
    }).join("");
  } catch (err) {
    listEl.innerHTML = `<div class="empty-state-small" style="padding:8px 10px; color:#ef4444; font-size:11px;">Failed to load models: ${escapeHtml(err.message)}</div>`;
  }
}

async function switchHermesModel(modelId, provider) {
  if (!modelId) return;
  const short = modelId.split("/").pop();
  setText("hermes-active-model-name", short);
  const isGoogle = (provider || "").toLowerCase().includes("gemini") || (provider || "").toLowerCase().includes("google") || modelId.toLowerCase().includes("gemini");
  setText("provider-prefix-label", isGoogle ? "GOOGLE ·" : "OPENROUTER ·");

  try {
    const res = await api("/api/hermes/model", {
      method: "POST",
      body: { model: modelId, provider: provider },
    });
    notify(res.message || `Switched AI Brain to ${modelId}`);
    if (typeof refresh === "function") await refresh();
    loadHermesOSState();
    loadSystemChanges();
  } catch (err) {
    showError("Failed to switch model: " + err.message);
  }
}

// --- System Notification Settings (Telegram Bot) ---
let currentRiskCaps = null;

async function loadRiskCapsSettings() {
  try {
    const data = await api("/api/caps");
    currentRiskCaps = data;
    const ksInput = $("caps-kill-switch");
    const ksStatus = $("caps-kill-switch-status");
    if (ksInput) {
      ksInput.checked = Boolean(data.kill_switch_active);
      if (ksStatus) {
        ksStatus.textContent = data.kill_switch_active ? "ACTIVE (BLOCKED)" : "OFF";
        ksStatus.style.color = data.kill_switch_active ? "#ef4444" : "#888";
      }
    }
    const maxOrder = $("caps-max-order");
    if (maxOrder && data.max_order_bdt != null) {
      maxOrder.value = data.max_order_bdt;
    }
    const maxSymbol = $("caps-max-symbol");
    if (maxSymbol && data.max_symbol_bdt != null) {
      maxSymbol.value = data.max_symbol_bdt;
    }
    const dailyBudget = $("caps-daily-budget");
    if (dailyBudget && data.daily_budget_bdt != null) {
      dailyBudget.value = data.daily_budget_bdt;
    }
    const maxOrders = $("caps-max-orders");
    if (maxOrders && data.max_orders_per_day != null) {
      maxOrders.value = data.max_orders_per_day;
    }
  } catch (err) {
    console.warn("Could not load risk caps settings:", err);
  }
}

async function saveRiskCapsSettings(e) {
  if (e) e.preventDefault();
  const ksInput = $("caps-kill-switch");
  const maxOrderInput = $("caps-max-order");
  const maxSymbolInput = $("caps-max-symbol");
  const dailyBudgetInput = $("caps-daily-budget");
  const maxOrdersInput = $("caps-max-orders");
  const statusMsg = $("caps-save-status");

  const newKillSwitch = ksInput ? ksInput.checked : false;
  const newMaxOrder = maxOrderInput && maxOrderInput.value ? parseFloat(maxOrderInput.value) : null;
  const newMaxSymbol = maxSymbolInput && maxSymbolInput.value ? parseFloat(maxSymbolInput.value) : null;
  const newDailyBudget = dailyBudgetInput && dailyBudgetInput.value ? parseFloat(dailyBudgetInput.value) : null;
  const newMaxOrders = maxOrdersInput && maxOrdersInput.value ? parseInt(maxOrdersInput.value, 10) : null;

  let isRaising = false;
  if (currentRiskCaps) {
    if (newMaxOrder != null && currentRiskCaps.max_order_bdt != null && newMaxOrder > currentRiskCaps.max_order_bdt) isRaising = true;
    if (newMaxSymbol != null && currentRiskCaps.max_symbol_bdt != null && newMaxSymbol > currentRiskCaps.max_symbol_bdt) isRaising = true;
    if (newDailyBudget != null && currentRiskCaps.daily_budget_bdt != null && newDailyBudget > currentRiskCaps.daily_budget_bdt) isRaising = true;
    if (newMaxOrders != null && currentRiskCaps.max_orders_per_day != null && newMaxOrders > currentRiskCaps.max_orders_per_day) isRaising = true;
    if (currentRiskCaps.kill_switch_active && !newKillSwitch) isRaising = true;
  }

  let confirmReq = false;
  if (isRaising) {
    const ok = window.confirm("Raising risk limits relaxes trading restrictions. Do you confirm this change?");
    if (!ok) return;
    confirmReq = true;
  }

  const payload = {
    kill_switch_active: newKillSwitch,
    confirm: confirmReq,
  };
  if (newMaxOrder != null) payload.max_order_bdt = newMaxOrder;
  if (newMaxSymbol != null) payload.max_symbol_bdt = newMaxSymbol;
  if (newDailyBudget != null) payload.daily_budget_bdt = newDailyBudget;
  if (newMaxOrders != null) payload.max_orders_per_day = newMaxOrders;

  try {
    const res = await api("/api/caps", {
      method: "POST",
      body: payload,
    });
    currentRiskCaps = res;
    if (statusMsg) {
      statusMsg.textContent = "Saved ✓";
      statusMsg.className = "save-status-msg success";
    }
    notify("Risk caps and safety limits updated successfully.");
    await loadRiskCapsSettings();
    setTimeout(() => {
      if (statusMsg && statusMsg.textContent === "Saved ✓") {
        statusMsg.textContent = "";
        statusMsg.className = "save-status-msg";
      }
    }, 2000);
  } catch (err) {
    if (statusMsg) {
      statusMsg.textContent = err.message || "Failed to update risk caps";
      statusMsg.className = "save-status-msg error";
    }
    showError(err.message);
  }
}

async function loadApiKeysSettings() {
  loadRiskCapsSettings();
  try {
    const data = await api("/api/settings/keys");
    const tgToken = $("key-telegram-token");
    if (tgToken) {
      if (data.telegram_bot_token_masked && !tgToken.value) {
        tgToken.placeholder = data.telegram_bot_token_masked;
      } else if (!tgToken.value) {
        tgToken.placeholder = "123456789:ABC... (optional)";
      }
    }
    const tgChat = $("key-telegram-chat");
    if (tgChat) {
      if (data.telegram_chat_id_masked && !tgChat.value) {
        tgChat.placeholder = data.telegram_chat_id_masked;
      } else if (!tgChat.value) {
        tgChat.placeholder = "Chat ID (optional)";
      }
    }
  } catch (err) {
    console.warn("Could not load notification settings:", err);
  }
}

async function saveApiKeysSettings(e) {
  if (e) e.preventDefault();
  const tgToken = $("key-telegram-token")?.value?.trim();
  const tgChat = $("key-telegram-chat")?.value?.trim();

  const payload = {};
  if (tgToken) payload.telegram_bot_token = tgToken;
  if (tgChat) payload.telegram_chat_id = tgChat;

  const statusMsg = $("keys-save-status");
  const saveBtn = $("btn-save-api-keys") || $("save-keys-btn");
  try {
    await api("/api/settings/keys", {
      method: "POST",
      body: payload,
    });
    if (statusMsg) {
      statusMsg.textContent = "Saved ✓";
      statusMsg.className = "save-status-msg success";
    }
    notify("Notification settings updated successfully");
    if (tgToken && $("key-telegram-token")) $("key-telegram-token").value = "";
    await loadApiKeysSettings();
    setTimeout(() => {
      if (statusMsg && statusMsg.textContent === "Saved ✓") {
        statusMsg.textContent = "";
        statusMsg.className = "save-status-msg";
      }
    }, 2000);
  } catch (err) {
    if (statusMsg) {
      statusMsg.textContent = err.message || "Failed to save settings";
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
      setText("op-username", user.username || res.operator_username || "Operator");
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
  } catch (e) { }
  closeOperatorProfile();
  const loginGate = $("login-gate-overlay");
  if (loginGate) loginGate.showModal();
  notify("Cockpit session locked");
}

function markKeysDirty() {
  const saveBtn = $("btn-save-api-keys") || $("save-keys-btn");
  const statusMsg = $("keys-save-status");
  if (saveBtn) saveBtn.disabled = false;
  if (statusMsg) {
    statusMsg.textContent = "Unsaved changes";
    statusMsg.className = "save-status-msg dirty";
  }
}

function initAuthAndSettings() {
  // Bind API keys form and dirty state
  const keysForm = $("api-keys-form");
  const saveBtn = $("btn-save-api-keys") || $("save-keys-btn");
  if (saveBtn) saveBtn.disabled = true;

  if (keysForm) {
    keysForm.addEventListener("submit", saveApiKeysSettings);
    keysForm.querySelectorAll("input").forEach((inp) => {
      inp.addEventListener("input", markKeysDirty);
      inp.addEventListener("change", markKeysDirty);
    });
  }

  // Bind Risk Caps & Kill Switch form
  const capsForm = $("risk-caps-form");
  if (capsForm) {
    capsForm.addEventListener("submit", saveRiskCapsSettings);
  }
  const ksToggle = $("caps-kill-switch");
  if (ksToggle) {
    ksToggle.addEventListener("change", () => {
      const ksStatus = $("caps-kill-switch-status");
      if (ksStatus) {
        ksStatus.textContent = ksToggle.checked ? "ACTIVE (BLOCKED)" : "OFF";
        ksStatus.style.color = ksToggle.checked ? "#ef4444" : "#888";
      }
    });
  }

  // Key visibility toggles (.key-toggle-btn and .key-toggle-reveal)
  document.querySelectorAll(".key-toggle-btn, .key-toggle-reveal").forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.target;
      const inp = $(targetId);
      if (inp) {
        inp.type = inp.type === "password" ? "text" : "password";
      }
    });
  });

  // Sync daily quota limit slider & number input
  const dailySlider = $("daily-limit-slider");
  const dailyInput = $("key-daily-limit");
  if (dailySlider && dailyInput) {
    dailySlider.addEventListener("input", (e) => {
      dailyInput.value = e.target.value;
    });
    dailyInput.addEventListener("input", (e) => {
      dailySlider.value = e.target.value;
    });
  }

  // Bind operator avatar & profile modal
  const avatarBtn = $("user-avatar-btn");
  if (avatarBtn) avatarBtn.addEventListener("click", openOperatorProfile);

  const opCloseBtn = $("op-close-btn");
  if (opCloseBtn) opCloseBtn.addEventListener("click", closeOperatorProfile);

  const opBackdrop = $("op-backdrop");
  if (opBackdrop) opBackdrop.addEventListener("click", closeOperatorProfile);

  const opModal = $("operator-modal");
  if (opModal) {
    opModal.addEventListener("click", (e) => {
      if (e.target === opModal) closeOperatorProfile();
    });
  }

  const lockBtn = $("lock-cockpit-btn");
  if (lockBtn) lockBtn.addEventListener("click", handleOperatorLogout);

  // Bind Login form & 1-click autofill
  const loginForm = $("login-form");
  if (loginForm) loginForm.addEventListener("submit", handleOperatorLogin);

  const autofillBtn = $("login-autofill-btn");
  if (autofillBtn) {
    autofillBtn.addEventListener("click", async () => {
      try {
        const res = await api("/api/auth/session");
        if (res && res.authenticated) {
          const loginGate = $("login-gate-overlay");
          if (loginGate && loginGate.open) loginGate.close();
          showToast("Session already verified", "info");
          return;
        }
      } catch (e) { }
      showToast("Please enter your operator credentials", "info");
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
                  ${c.trading_mode ? `<span class="diff-mode-tag ${c.trading_mode === "TEST_OFFHOURS" ? "test-mode" : "live-mode"}">${escapeHtml(c.trading_mode === "TEST_OFFHOURS" ? "Test Mode 24/7" : "Live Hours (virtual)")}</span>` : ""}
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

// Chat prompt and form listener wiring
function initHermesChatListeners() {
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => sendChat(button.dataset.prompt));
  });
  const chatForm = $("chat-form");
  if (chatForm) {
    chatForm.addEventListener("submit", (event) => {
      event.preventDefault();
      const inp = $("chat-input");
      if (inp) sendChat(inp.value);
    });
  }
  const chatInput = $("chat-input");
  if (chatInput) {
    chatInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        sendChat(chatInput.value);
      }
    });
  }

  // Model display in status bar
  const modelBtn = $("hermes-model-trigger") || $("hermes-bottom-model-btn") || $("hermes-model-btn");
  const modelDrop = $("model-dropup-menu");
  if (modelBtn) {
    modelBtn.onclick = (e) => {
      window.toggleHermesModelPicker(e);
    };
  }
  if (modelDrop) {
    document.addEventListener("click", (e) => {
      if (modelBtn && !modelDrop.contains(e.target) && !modelBtn.contains(e.target)) {
        modelDrop.hidden = true;
        modelBtn.setAttribute("aria-expanded", "false");
      }
    });
  }

  // Rollback buttons
  const rbPaneBtn = $("rollback-pane-btn");
  if (rbPaneBtn) rbPaneBtn.addEventListener("click", executeRollback);
  const rbSkillsBtn = $("rollback-skills-btn");
  if (rbSkillsBtn) rbSkillsBtn.addEventListener("click", executeRollback);

  // StockNow Live Session Action Buttons with spinner & toast feedback
  const setStockNowBusy = (isBusy) => {
    const actionButtons = document.querySelectorAll(".stocknow-live-actions button");
    actionButtons.forEach(b => { b.disabled = isBusy; });
  };

  const updateSourceBadgeToLive = (portfolioId = "164580") => {
    const sourceBadge = $("source-badge");
    if (sourceBadge) {
      sourceBadge.className = "stream-badge";
      sourceBadge.innerHTML = `<span class="status-dot live-dot"></span> STOCKNOW LIVE (#${portfolioId})`;
    }
  };

  const runBridgeAction = async (btn, loadingLabel, defaultLabel, actionFn) => {
    setStockNowBusy(true);
    btn.classList.add("is-loading");
    btn.innerHTML = `<span class="btn-spinner"></span> ${loadingLabel}`;
    try {
      await actionFn();
    } finally {
      btn.classList.remove("is-loading");
      btn.textContent = defaultLabel;
      setStockNowBusy(false);
    }
  };

  const btnLaunch = $("btn-stocknow-launch");
  if (btnLaunch) {
    btnLaunch.addEventListener("click", () => runBridgeAction(btnLaunch, "Launching...", "Launch Live Browser", async () => {
      try {
        const res = await api("/api/stocknow/session", { method: "POST", body: { action: "launch", mode: "ONSCREEN_LIVE" } });
        if (res.connected === false || res.state === "ERROR") {
          showError(res.reason || res.last_error || "Browser launch failed");
          return;
        }
        updateSourceBadgeToLive(res.bound_portfolio_id || res.auth?.bound_portfolio_id || "164580");
        notify("StockNow Live Browser launched and connected to #164580!");
        if (typeof refresh === "function") await refresh();
      } catch (err) {
        showError("Failed to launch browser: " + err.message);
      }
    }));
  }

  const btnAuth = $("btn-stocknow-auth");
  if (btnAuth) {
    btnAuth.addEventListener("click", () => runBridgeAction(btnAuth, "Checking...", "Check / Auto-Login", async () => {
      try {
        const res = await api("/api/stocknow/session", { method: "POST", body: { action: "check_auth" } });
        if (res.authenticated === false || res.state === "ERROR") {
          showError(res.reason || res.message || "Auth check failed");
          return;
        }
        updateSourceBadgeToLive(res.bound_portfolio_id || "164580");
        notify(res.message || "Persistent session is authenticated.");
        if (typeof refresh === "function") await refresh();
      } catch (err) {
        showError("Auth check failed: " + err.message);
      }
    }));
  }

  const btnSync = $("btn-stocknow-sync");
  if (btnSync) {
    btnSync.addEventListener("click", () => runBridgeAction(btnSync, "Syncing...", "Sync Live Prices", async () => {
      try {
        const res = await api("/api/stocknow/sync-market", { method: "POST", body: {} });
        const count = res.result?.synced_count ?? 0;
        notify(`Synchronized ${count} live DSE quotes into database.`);
        if (typeof refresh === "function") await refresh();
      } catch (err) {
        showError("Sync failed: " + err.message);
      }
    }));
  }

  const btnSyncPortfolio = $("btn-stocknow-sync-portfolio");
  if (btnSyncPortfolio) {
    btnSyncPortfolio.addEventListener("click", () => runBridgeAction(btnSyncPortfolio, "Syncing Portfolio...", 'Sync "Humming Bird" Portfolio', async () => {
      try {
        const res = await api("/api/stocknow/sync-portfolio", { method: "POST", body: {} });
        if (res.result && res.result.success === false) {
          showError(res.result.reason || "Portfolio sync failed");
          return;
        }
        updateSourceBadgeToLive(res.result?.portfolio_id || "164580");
        const count = res.result?.synced_holdings_count ?? 0;
        const cash = res.result?.cash_balance ?? 0;
        notify(`Synchronized Humming Bird portfolio: ${count} holdings, ৳${Number(cash).toLocaleString()} cash.`);
        if (typeof refresh === "function") await refresh();
      } catch (err) {
        showError("Portfolio sync failed: " + err.message);
      }
    }));
  }

  const btnLogout = $("btn-stocknow-logout");
  if (btnLogout) {
    btnLogout.addEventListener("click", () => runBridgeAction(btnLogout, "Logging out...", "Log Out (Test)", async () => {
      try {
        const res = await api("/api/stocknow/session", { method: "POST", body: { action: "logout" } });
        notify(res.message || "Logged out from StockNow test session.");
        if (typeof refresh === "function") await refresh();
      } catch (err) {
        showError("Logout failed: " + err.message);
      }
    }));
  }
}

// Wrap initHermesSidebar to also init chat listeners and active conversation
const _origInitHermesSidebar = initHermesSidebar;
initHermesSidebar = function () {
  if (typeof localStorage !== "undefined" && typeof state !== "undefined") {
    // state.activeConversationId is initialized inside initHermesSidebar()
  }
  _origInitHermesSidebar();
  initHermesChatListeners();
};
