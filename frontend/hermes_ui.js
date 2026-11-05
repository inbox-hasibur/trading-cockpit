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

function addMessage(role, content, provider = null, servedBy = null) {
  const article = element("article", `chat-message ${role}`);
  const author = element("div", "message-author");
  if (role === "assistant") author.append(element("span", "assistant-avatar", "✦"));
  author.append(document.createTextNode(role === "user" ? "YOU" : "HERMES"));
  if (servedBy && servedBy.provider && servedBy.model) {
    const cleanModel = String(servedBy.model).replace(/^google\//, "");
    author.append(element("span", "muted", `· ${servedBy.provider} · ${cleanModel}`));
  } else if (provider) {
    author.append(element("span", "muted", `· ${provider.toUpperCase()}`));
  }
  const body = element("div", "message-body");
  body.innerHTML = formatChatMarkdown(content);
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
    const servedBy = response.served_by || {
      tier: response.provider === "local" ? 3 : (response.provider === "gemini" ? 2 : 1),
      provider: (response.provider || "local").toUpperCase(),
      model: response.model || "hermes-local-quant",
      fallback_reason: null,
    };
    const article = addMessage("assistant", response.reply, null, servedBy);

    if (response.warning || servedBy.fallback_reason) {
      let warnText = response.warning || "Served via offline fallback";
      if (servedBy.fallback_reason && !warnText.toLowerCase().includes(servedBy.fallback_reason.toLowerCase())) {
        warnText += ` (Trigger: ${servedBy.fallback_reason})`;
      }
      article.append(element("p", "response-warning", warnText));
    }

    state.lastChatProvider = response.provider;
    const cleanModel = String(servedBy.model || "").replace(/^google\//, "");
    if (servedBy.provider === "LOCAL") {
      setText("chat-provider", "LOCAL SUMMARY · NO API COST FOR THIS REPLY");
      setText("chat-footer-note", "Read-only local summary. No trade or rule changes made.");
    } else {
      setText("chat-provider", `${servedBy.provider} · ${cleanModel}`);
      setText("chat-footer-note", "External AI used demo portfolio context. No execution tools.");
    }

    // Keep bottom composer footer (#hermes-model-trigger) showing the selected primary model,
    // and set its title tooltip to "Last reply served by: <provider> (<model>)"
    const modelTrigger = $("hermes-model-trigger");
    if (modelTrigger) {
      modelTrigger.title = `Last reply served by: ${servedBy.provider} (${cleanModel})`;
    }

    // Refresh settings & quota counters so both spots update immediately
    loadApiKeysSettings();

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

// --- Hermes IDE Resizable Sidebar, Tabs & Antigravity History ---
function initHermesSidebar() {
  const sidebar = $("hermes-sidebar");
  const resizer = $("hermes-resizer") || $("hermes-resize-handle");
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
    const isGemini = active.startsWith("google/") || active.startsWith("gemini");
    const isLocal = active === "local-quant-brain";
    setText("provider-prefix-label", isGemini ? "GEMINI ·" : (isLocal ? "LOCAL ·" : "OPENROUTER ·"));

    // Sync dropdown menu
    const dropdownList = $("model-dropdown-list");
    if (dropdownList) {
      dropdownList.innerHTML = models.map((m) => {
        const isCur = m.id === active;
        return `
          <button type="button" class="model-dropup-item ${isCur ? "is-active" : ""}" data-model="${escapeHtml(m.id)}">
            <span class="model-item-name">${escapeHtml(m.name)}</span>
            ${isCur ? '<span class="model-dropup-check">✓</span>' : ""}
          </button>
        `;
      }).join("");

      dropdownList.querySelectorAll(".model-dropup-item").forEach((btn) => {
        btn.addEventListener("click", () => {
          const modId = btn.dataset.model;
          const drop = $("model-dropup-menu") || $("model-picker-dropdown");
          if (drop) drop.hidden = true;
          switchHermesModel(modId);
        });
      });
    }

    // Sync Settings select
    const select = $("settings-model-select");
    if (select) {
      select.innerHTML = models.map((m) => `<option value="${escapeHtml(m.id)}">${escapeHtml(m.name)}</option>`).join("");
      if (active && !Array.from(select.options).some((opt) => opt.value === active)) {
        const opt = document.createElement("option");
        opt.value = active;
        opt.textContent = `${active} (Active)`;
        select.prepend(opt);
      }
      select.value = active;
    }
    const errHint = $("settings-model-hint") || $("settings-model-error");
    if (errHint) errHint.hidden = true;

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
    const select = $("settings-model-select");
    if (select) {
      select.innerHTML = '<option disabled selected>Models unavailable</option>';
    }
    const errHint = $("settings-model-hint") || $("settings-model-error");
    if (errHint) {
      errHint.textContent = "Unable to load model list. Please check connection.";
      errHint.hidden = false;
    }
  }
}

async function switchHermesModel(modelId) {
  if (!modelId || state.busy) return;
  state.busy = true;
  updateControls();
  // Immediately synchronize both controls
  const short = modelId.split("/").pop();
  setText("hermes-active-model-name", short);
  const select = $("settings-model-select");
  if (select && select.value !== modelId) {
    if (!Array.from(select.options).some((opt) => opt.value === modelId)) {
      const opt = document.createElement("option");
      opt.value = modelId;
      opt.textContent = `${modelId} (Active)`;
      select.prepend(opt);
    }
    select.value = modelId;
  }
  const tier1Label = $("tier1-label");
  if (tier1Label) tier1Label.textContent = modelId;
  const dropdownList = $("model-dropdown-list");
  if (dropdownList) {
    dropdownList.querySelectorAll(".model-dropup-item").forEach((btn) => {
      const isCur = btn.dataset.model === modelId;
      btn.classList.toggle("is-active", isCur);
      const check = btn.querySelector(".model-dropup-check");
      if (isCur && !check) {
        const sp = document.createElement("span");
        sp.className = "model-dropup-check";
        sp.textContent = "✓";
        btn.append(sp);
      } else if (!isCur && check) {
        check.remove();
      }
    });
  }
  try {
    const res = await api("/api/hermes/model", {
      method: "POST",
      body: { model: modelId },
    });
    notify(`AI Brain switched to ${modelId}`);
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

// --- API Keys, Quotas & Telemetry Settings ---
async function loadApiKeysSettings() {
  try {
    const data = await api("/api/settings/keys");
    const hasOr = Boolean(data.openrouter_configured || data.has_openrouter_key || data.openrouter_key_masked);
    const hasGemini = Boolean(data.gemini_configured || data.has_gemini_key || data.gemini_key_masked);
    const hintOr = $("hint-openrouter");
    if (hintOr) {
      hintOr.textContent = hasOr ? "● Connected (Masked)" : "○ Not set";
      hintOr.className = `key-status-badge ${hasOr ? "configured" : "empty"}`;
    }
    const hintGemini = $("hint-gemini");
    if (hintGemini) {
      hintGemini.textContent = hasGemini ? "● Connected (Masked)" : "○ Not set";
      hintGemini.className = `key-status-badge ${hasGemini ? "configured" : "empty"}`;
    }

    const orInput = $("key-openrouter");
    if (orInput && hasOr && !orInput.value) {
      orInput.placeholder = data.openrouter_key_masked || "sk-or-v1-••••••••";
    }
    const geminiInput = $("key-gemini");
    if (geminiInput && hasGemini && !geminiInput.value) {
      geminiInput.placeholder = data.gemini_key_masked || "AIzaSy••••••••";
    }
    const tgToken = $("key-telegram-token");
    if (tgToken) {
      if (data.telegram_bot_token_masked && !tgToken.value) {
        tgToken.placeholder = data.telegram_bot_token_masked;
      } else if (!tgToken.value) {
        tgToken.placeholder = "123456789:ABC... (optional)";
      }
      if (!data.telegram_bot_token_masked && !tgToken.value) {
        tgToken.value = "";
      }
    }
    const tgChat = $("key-telegram-chat");
    if (tgChat) {
      if (data.telegram_chat_id_masked && !tgChat.value) {
        tgChat.placeholder = data.telegram_chat_id_masked;
      } else if (!tgChat.value) {
        tgChat.placeholder = "Chat ID (optional)";
      }
      if (!data.telegram_chat_id && !data.telegram_chat_id_masked) {
        tgChat.value = "";
      }
    }
    const limitVal = data.daily_call_limit || 30;
    const limitInput = $("key-daily-limit");
    if (limitInput) limitInput.value = limitVal;
    const limitSlider = $("daily-limit-slider");
    if (limitSlider) limitSlider.value = limitVal;

    // Telemetry quota bar & settings budget text (unified single source of truth)
    const callsUsed = data.daily_calls_used !== undefined ? data.daily_calls_used : (data.calls_used_today || 0);
    const limit = data.daily_call_limit || 30;
    const pct = Math.min(100, Math.round((callsUsed / limit) * 100));
    const budgetStr = `${callsUsed} / ${limit} calls used`;
    setText("telemetry-usage-text", budgetStr);
    setText("settings-budget-text", budgetStr);
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
    if (saveBtn) {
      saveBtn.disabled = true;
    }
    notify("API Keys & Quotas updated successfully");
    if (orKey && $("key-openrouter")) $("key-openrouter").value = "";
    if (geminiKey && $("key-gemini")) $("key-gemini").value = "";
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
      statusMsg.textContent = err.message || "Failed to save configuration";
      statusMsg.className = "save-status-msg error";
    }
    if (saveBtn) {
      saveBtn.disabled = false;
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

  // Model Picker Drop-up toggle
  const modelBtn = $("hermes-model-trigger") || $("hermes-bottom-model-btn") || $("hermes-model-btn");
  const modelDrop = $("model-dropup-menu") || $("model-picker-dropdown");
  if (modelBtn && modelDrop) {
    modelBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      modelDrop.hidden = !modelDrop.hidden;
    });
    document.addEventListener("click", (e) => {
      if (!modelDrop.contains(e.target) && !modelBtn.contains(e.target)) {
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

  // StockNow Live Session Action Buttons
  const btnLaunch = $("btn-stocknow-launch");
  if (btnLaunch) {
    btnLaunch.addEventListener("click", async () => {
      try {
        btnLaunch.disabled = true;
        btnLaunch.textContent = "Launching…";
        const res = await api("/api/stocknow/session", { method: "POST", body: { action: "launch", mode: "ONSCREEN_LIVE" } });
        notify(res.connected ? "StockNow live browser launched (READY)." : (res.reason || "Browser launched."));
      } catch (err) {
        notify("Failed to launch browser: " + err.message, true);
      } finally {
        btnLaunch.disabled = false;
        btnLaunch.textContent = "Launch Live Browser";
      }
    });
  }

  const btnAuth = $("btn-stocknow-auth");
  if (btnAuth) {
    btnAuth.addEventListener("click", async () => {
      try {
        btnAuth.disabled = true;
        btnAuth.textContent = "Checking…";
        const res = await api("/api/stocknow/session", { method: "POST", body: { action: "check_auth" } });
        notify(res.message || "Auth checked.");
      } catch (err) {
        notify("Auth check failed: " + err.message, true);
      } finally {
        btnAuth.disabled = false;
        btnAuth.textContent = "Check / Auto-Login";
      }
    });
  }

  const btnSync = $("btn-stocknow-sync");
  if (btnSync) {
    btnSync.addEventListener("click", async () => {
      try {
        btnSync.disabled = true;
        btnSync.textContent = "Syncing…";
        const res = await api("/api/stocknow/sync-market", { method: "POST", body: {} });
        const count = res.result?.synced_count ?? 0;
        notify(`Synchronized ${count} live DSE quotes into database.`);
        if (typeof refresh === "function") await refresh();
      } catch (err) {
        notify("Sync failed: " + err.message, true);
      } finally {
        btnSync.disabled = false;
        btnSync.textContent = "Sync Live Prices";
      }
    });
  }

  const btnSyncPortfolio = $("btn-stocknow-sync-portfolio");
  if (btnSyncPortfolio) {
    btnSyncPortfolio.addEventListener("click", async () => {
      try {
        btnSyncPortfolio.disabled = true;
        btnSyncPortfolio.textContent = "Syncing Portfolio…";
        const res = await api("/api/stocknow/sync-portfolio", { method: "POST", body: {} });
        const count = res.result?.synced_holdings_count ?? 0;
        const cash = res.result?.cash_balance ?? 0;
        notify(`Synchronized Humming Bird portfolio: ${count} holdings, ৳${Number(cash).toLocaleString()} cash.`);
        if (typeof refresh === "function") await refresh();
      } catch (err) {
        notify("Portfolio sync failed: " + err.message, true);
      } finally {
        btnSyncPortfolio.disabled = false;
        btnSyncPortfolio.textContent = 'Sync "Humming Bird" Portfolio';
      }
    });
  }
}

// Wrap initHermesSidebar to also init chat listeners and active conversation
const _origInitHermesSidebar = initHermesSidebar;
initHermesSidebar = function() {
  if (typeof localStorage !== "undefined" && typeof state !== "undefined") {
    // state.activeConversationId is initialized inside initHermesSidebar()
  }
  _origInitHermesSidebar();
  initHermesChatListeners();
};
