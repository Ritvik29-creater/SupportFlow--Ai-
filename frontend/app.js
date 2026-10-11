/**
 * SupportFlow AI v3 — Intelligent Chat Frontend
 * LangGraph Multi-Agent · RAG · Human-in-the-Loop
 */

const API_BASE = "";  // Same origin — served by FastAPI
let SESSION_ID = "sess_" + Math.random().toString(36).substring(2, 11);
let IS_WAITING = false;

// ── DOM Refs ──────────────────────────────────────────────────────────────────
const messages     = document.getElementById("messages");
const chatForm     = document.getElementById("chat-form");
const userInput    = document.getElementById("user-input");
const sendBtn      = document.getElementById("send-btn");
const clearBtn     = document.getElementById("clear-btn");
const scenarios    = document.getElementById("scenarios");
const sidebarToggle = document.getElementById("sidebar-toggle");
const sidebar      = document.querySelector(".sidebar");

// Pipeline nodes
const nodes = {
  guard:      document.getElementById("node-guard"),
  sentiment:  document.getElementById("node-sentiment"),
  intent:     document.getElementById("node-intent"),
  rag:        document.getElementById("node-rag"),
  specialist: document.getElementById("node-specialist"),
  resolution: document.getElementById("node-resolution"),
  confidence: document.getElementById("node-confidence"),
};
const descs = {
  guard:      document.getElementById("desc-guard"),
  sentiment:  document.getElementById("desc-sentiment"),
  intent:     document.getElementById("desc-intent"),
  rag:        document.getElementById("desc-rag"),
  specialist: document.getElementById("desc-specialist"),
  resolution: document.getElementById("desc-resolution"),
  confidence: document.getElementById("desc-confidence"),
};

// Side panel refs
const intentCard    = document.getElementById("intent-card");
const intentBadge   = document.getElementById("intent-badge");
const sentimentCard = document.getElementById("sentiment-card");
const sentimentBadge= document.getElementById("sentiment-badge");
const statusInd     = document.getElementById("status-indicator");
const statusLabel   = document.getElementById("status-label");

// ── Intent metadata ───────────────────────────────────────────────────────────
const INTENT_META = {
  order_tracking:      { icon: "🛵", label: "Order Tracking",      agent: "Order Agent",        color: "#f59e0b" },
  payment:             { icon: "💳", label: "Payment Issue",       agent: "Payment Agent",      color: "#3b82f6" },
  refund:              { icon: "💰", label: "Refund Request",      agent: "Refund Agent",       color: "#22c55e" },
  restaurant:          { icon: "🍽️", label: "Restaurant Issue",    agent: "Restaurant Agent",   color: "#f97316" },
  delivery_partner:    { icon: "🚴", label: "Delivery Partner",    agent: "Partner Agent",      color: "#ef4444" },
  account_app:         { icon: "📱", label: "Account & App",       agent: "App Agent",          color: "#8b5cf6" },
  coupon_offer:        { icon: "🎟️", label: "Coupon & Offers",     agent: "Offers Agent",       color: "#ec4899" },
  visual_verification: { icon: "📸", label: "Visual Verification", agent: "Vision Agent",       color: "#a855f7" },
  general_support:     { icon: "📚", label: "General Support",     agent: "RAG Agent",          color: "#94a3b8" },
  unknown:             { icon: "❓", label: "Analyzing...",         agent: "RAG Agent",          color: "#94a3b8" },
};

const SENTIMENT_META = {
  very_upset:      { icon: "😠", label: "Very Upset",       color: "#ef4444" },
  frustrated:      { icon: "😤", label: "Frustrated",       color: "#f59e0b" },
  sad_disappointed:{ icon: "😔", label: "Disappointed",     color: "#8b5cf6" },
  urgent:          { icon: "⚡", label: "Urgent",           color: "#ef4444" },
  neutral:         { icon: "😐", label: "Neutral",          color: "#94a3b8" },
  positive:        { icon: "😊", label: "Positive",         color: "#22c55e" },
};

// ── Sidebar toggle (mobile) ───────────────────────────────────────────────────
if (sidebarToggle) {
  sidebarToggle.addEventListener("click", () => {
    if (sidebar) sidebar.classList.toggle("open");
  });
}

document.addEventListener("click", (e) => {
  if (sidebar && sidebar.classList.contains("open") &&
      !sidebar.contains(e.target) && sidebarToggle && e.target !== sidebarToggle) {
    sidebar.classList.remove("open");
  }
});

// ── Scenario chips ────────────────────────────────────────────────────────────
document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    const msg = chip.dataset.msg;
    if (msg) {
      userInput.value = msg;
      autoResize();
      userInput.focus();
      scenarios.style.opacity = "0.3";
    }
  });
});

// ── Textarea auto-resize ──────────────────────────────────────────────────────
userInput.addEventListener("input", autoResize);
function autoResize() {
  userInput.style.height = "auto";
  userInput.style.height = Math.min(userInput.scrollHeight, 130) + "px";
}

// Enter = submit, Shift+Enter = newline
userInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

// ── Clear chat ────────────────────────────────────────────────────────────────
clearBtn.addEventListener("click", () => {
  messages.innerHTML = "";
  SESSION_ID = "sess_" + Math.random().toString(36).substring(2, 11);
  resetPipeline();
  confCard.style.display = "none";
  intentCard.style.display = "none";
  sentimentCard.style.display = "none";
  scenarios.style.opacity = "1";
  scenarios.style.display = "";
  appendWelcome();
  fetch(`/api/chat/session/${SESSION_ID}`, { method: "DELETE" }).catch(() => {});
});

// ── Form submit ───────────────────────────────────────────────────────────────
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = userInput.value.trim();

  if (!query || IS_WAITING) return;

  IS_WAITING = true;
  sendBtn.disabled = true;
  scenarios.style.display = "none";

  appendUserMsg(query);
  userInput.value = "";
  userInput.style.height = "auto";

  const typingId = appendTyping();
  animatePipeline();

  try {
    const res = await fetch(`/api/chat/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        content: query,
        session_id: SESSION_ID,
      }),
    });

    removeTyping(typingId);

    if (res.ok) {
      const data = await res.json();
      finishPipeline(data);
      appendBotMsg(data.answer, data);
      setOnline();
    } else {
      const err = await res.json().catch(() => ({}));
      finishPipelineError();
      appendBotMsg(
        "I'm having trouble reaching the AI pipeline right now. Please try again in a moment.",
        { action: "error", confidence: 0 }
      );
      setOffline();
    }
  } catch (err) {
    removeTyping(typingId);
    finishPipelineError();
    appendBotMsg(
      "Unable to connect to the server. Please make sure the backend is running at http://localhost:8000",
      { action: "error", confidence: 0 }
    );
    setOffline();
  } finally {
    IS_WAITING = false;
    sendBtn.disabled = false;
    userInput.focus();
  }
});


// ── Status ────────────────────────────────────────────────────────────────────
function setOnline() {
  statusInd.className = "status-indicator online";
  statusLabel.textContent = "AI Online";
}
function setOffline() {
  statusInd.className = "status-indicator offline";
  statusLabel.textContent = "Offline";
}

// Check server health on load
async function checkHealth() {
  try {
    const r = await fetch("/api/chat/health", { signal: AbortSignal.timeout(3000) });
    if (r.ok) setOnline();
    else setOffline();
  } catch {
    setOffline();
  }
}
checkHealth();

// ── Pipeline Animation ────────────────────────────────────────────────────────
let _pipelineTimers = [];

function resetPipeline() {
  _pipelineTimers.forEach(clearTimeout);
  _pipelineTimers = [];
  Object.values(nodes).forEach(n => { if (n) n.dataset.state = "idle"; });
}

function setNodeState(key, state, desc = null) {
  const node = nodes[key];
  if (node) node.dataset.state = state;
  if (desc && descs[key]) descs[key].textContent = desc;
}

function animatePipeline(hasPhoto = false) {
  resetPipeline();

  const schedule = (fn, delay) => {
    const t = setTimeout(fn, delay);
    _pipelineTimers.push(t);
  };

  setNodeState("sentiment", "running", "Analyzing customer mood...");
  schedule(() => {
    setNodeState("sentiment", "done", "Emotion calibrated");
    setNodeState("intent", "running", "Classifying issue intent...");
  }, 250);
  schedule(() => {
    setNodeState("intent", "done", "Intent determined");
    setNodeState("specialist", "running", "Querying domain specialist...");
  }, 600);
  schedule(() => {
    setNodeState("specialist", "done", "Domain knowledge retrieved");
    setNodeState("resolution", "running", "Evaluating restaurant & situation rules...");
  }, 1100);
  // specialist, resolution, and confidence complete when response arrives
}

function finishPipeline(data) {
  _pipelineTimers.forEach(clearTimeout);
  _pipelineTimers = [];

  const intent = data.intent || "general_support";
  const meta = INTENT_META[intent] || INTENT_META.general_support;

  setNodeState("specialist", "done", meta.agent || "Specialist Active");
  if (data.resolution_details) {
    const res = data.resolution_details;
    const tierShort = res.tier ? res.tier.split("—")[0].replace("Guarantee", "").trim() : "Policy Evaluated";
    setNodeState("resolution", "done", tierShort);
  } else {
    setNodeState("resolution", "done", "Rules Verified");
  }
  setNodeState("confidence", "running", "Verifying resolution...");

  const isEscalate = data.action === "escalate";

  setTimeout(() => {
    setNodeState("confidence", isEscalate ? "error" : "done",
      isEscalate ? "Escalating to human" : "Resolution Verified");

    // Update specialist node info
    const specIcon = document.getElementById("specialist-icon");
    const specName = document.getElementById("specialist-name");
    if (specIcon) specIcon.textContent = meta.icon;
    if (specName) specName.textContent = meta.agent;

    // Intent card
    intentCard.style.display = "block";
    intentBadge.textContent = meta.icon + " " + meta.label;

    // Sentiment card
    if (data.sentiment) {
      const sm = SENTIMENT_META[data.sentiment] || SENTIMENT_META.neutral;
      sentimentCard.style.display = "block";
      sentimentBadge.textContent = sm.icon + " " + sm.label;
      sentimentBadge.style.color = sm.color;
    }
  }, 400);
}


function finishPipelineError() {
  _pipelineTimers.forEach(clearTimeout);
  _pipelineTimers = [];
  Object.values(nodes).forEach(n => {
    if (n && n.dataset.state === "running") n.dataset.state = "error";
  });
}

// ── Message Rendering ─────────────────────────────────────────────────────────
function now() {
  return new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function appendWelcome() {
  const row = document.createElement("div");
  row.className = "msg-row bot";
  row.innerHTML = `
    <div class="avatar bot-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
    </div>
    <div class="msg-content">
      <div class="bubble bot-bubble">
        <p>👋 Hey! I'm <strong>SupportFlow AI</strong> — your intelligent food delivery support agent, powered by LLaMA 3.3 70B and a full multi-agent LangGraph pipeline.</p>
        <p>Tell me your issue in plain English — <strong>no order ID needed</strong>. I understand context, emotion, and intent automatically.</p>
        <p>I handle <strong>refunds</strong>, <strong>late deliveries</strong>, <strong>missing items</strong>, <strong>payment disputes</strong>, <strong>restaurant complaints</strong>, and more. For complex cases, I'll connect you with a real human agent instantly.</p>
      </div>
      <div class="msg-time">${now()}</div>
    </div>
  `;
  messages.appendChild(row);
}

function appendUserMsg(text) {
  const row = document.createElement("div");
  row.className = "msg-row user";
  row.innerHTML = `
    <div class="avatar user-avatar">👤</div>
    <div class="msg-content">
      <div class="bubble user-bubble">
        <div>${escHtml(text)}</div>
      </div>
      <div class="msg-time">${now()}</div>
    </div>
  `;
  messages.appendChild(row);
  scrollDown();
}

function appendBotMsg(text, meta = {}) {
  const row = document.createElement("div");
  row.className = "msg-row bot";

  const textStr = typeof text === "string" ? text : (text != null ? String(text) : "");
  const textLower = textStr.toLowerCase();

  const intent = meta.intent || "general_support";
  const intMeta = INTENT_META[intent] || INTENT_META.general_support;

  // Situation & Restaurant Policy Resolution Card
  let resolutionCardHtml = "";
  if (meta.resolution_details) {
    const res = meta.resolution_details;
    const isApproved = res.decision === "APPROVE_FULL_REFUND" || res.decision === "APPROVE_PARTIAL_REFUND";
    const badgeClass = res.decision === "APPROVE_FULL_REFUND" ? "visual-badge-approved" : (res.decision === "APPROVE_PARTIAL_REFUND" ? "visual-badge-partial" : "visual-badge-rejected");
    const badgeTitle = isApproved ? `⚖️ ${res.tier}` : `❌ ${res.tier}`;

    resolutionCardHtml = `
      <div class="visual-verification-badge ${badgeClass}">
        ${escHtml(badgeTitle)}
      </div>
      <div class="visual-card-grid">
        <div class="visual-grid-item">
          <span class="visual-grid-label">Resolution Policy</span>
          <span class="visual-grid-val">${escHtml(res.decision === 'APPROVE_FULL_REFUND' ? '100% Full Compensation' : (res.decision === 'APPROVE_PARTIAL_REFUND' ? `${res.refund_pct}% Courtesy Compensation` : 'Ineligible Cancellation'))}</span>
        </div>
        <div class="visual-grid-item">
          <span class="visual-grid-label">Authorized Refund</span>
          <span class="visual-grid-val" style="color: #4ade80;">₹${Number(res.refund_amount || 0).toFixed(2)}</span>
        </div>
        <div class="visual-grid-item">
          <span class="visual-grid-label">Proof Mode</span>
          <span class="visual-grid-val" style="color: #38bdf8;">Telemetric &amp; Conversational (No Photos)</span>
        </div>
        <div class="visual-grid-item">
          <span class="visual-grid-label">Voucher / Code</span>
          <span class="visual-grid-val" style="color: #ec4899;">${escHtml(res.voucher_code || 'None')}</span>
        </div>
      </div>
    `;
  }

  // Tags
  const tags = [];
  if (meta.intent && meta.intent !== "unknown") {
    tags.push(`<span class="tag tag-intent">${intMeta.icon} ${intMeta.label}</span>`);
  }
  if (meta.agent_used) {
    tags.push(`<span class="tag tag-agent">🤖 ${meta.agent_used.replace("_", " ")}</span>`);
  }
  if (meta.ticket_id) {
    tags.push(`<span class="tag tag-ticket">🎫 ${meta.ticket_id}</span>`);
  }

  const tagsHtml = tags.length
    ? `<div class="msg-tags">${tags.join("")}</div>` : "";

  // Escalation card
  let escHtml_ = "";
  if (meta.action === "escalate" && meta.ticket_id) {
    escHtml_ = `
      <div class="escalation-card">
        <div class="esc-header">🧑‍💼 Escalated to Human Agent</div>
        <div class="esc-info">Ticket ${meta.ticket_id} · Human specialist will respond within 2–4 hrs</div>
      </div>`;
  }

  // Voucher Toast Card
  let voucherHtml = "";
  const voucherMatch = textStr.match(/`([A-Z0-9]{3,}-[A-Z0-9]+)`/);
  if (voucherMatch && (textLower.includes("voucher") || textLower.includes("coupon") || textLower.includes("courtesy") || textLower.includes("warm25") || textLower.includes("ontime") || textLower.includes("respect200") || textLower.includes("salan") || textLower.includes("melt"))) {
    const vCode = voucherMatch[1];
    voucherHtml = `
      <div class="voucher-toast-card">
        <div class="voucher-toast-icon">🎟️</div>
        <div class="voucher-toast-details">
          <div class="voucher-toast-title">APOLOGY VOUCHER ISSUED</div>
          <div class="voucher-toast-code" onclick="navigator.clipboard.writeText('${vCode}'); alert('Voucher code copied: ${vCode}')">
            ${vCode} <span class="copy-hint">(Click to copy)</span>
          </div>
        </div>
      </div>
    `;
  }

  // Contextual quick action buttons
  const chips = [];

  // Options from resolution_details if provided
  if (meta.resolution_details && Array.isArray(meta.resolution_details.interactive_options)) {
    for (const opt of meta.resolution_details.interactive_options) {
      let replyMsg = `Yes, please process the ${opt.method} option for my order.`;
      if (opt.method === "wallet") {
        replyMsg = `Yes, please credit the refund of ₹${Number(meta.resolution_details.refund_amount || 0).toFixed(2)} to my SupportFlow wallet.`;
      } else if (opt.method === "voucher") {
        replyMsg = `I choose the apology voucher ${meta.resolution_details.voucher_code || ''} for my next order.`;
      } else if (opt.method === "bank") {
        replyMsg = `Please refund to my original payment method.`;
      } else if (opt.method === "track") {
        replyMsg = `Where is my order right now? Can you check live status?`;
      } else if (opt.method === "escalate") {
        replyMsg = `The gravy spilled completely and ruined the entire meal, I request a full refund.`;
      }
      chips.push({ label: opt.label, msg: replyMsg });
    }
  }

  // Common interactive options if bot presented Option 1 / Option 2
  if ((textLower.includes("option 1") || textLower.includes("option 2") || textLower.includes("which option")) && !chips.length) {
    chips.push({ label: "⚡ Option 1: Credit to Wallet", msg: "I choose Option 1: Process the courtesy refund to my wallet." });
    chips.push({ label: "🎟️ Option 2: Claim Voucher", msg: "I choose Option 2: Send me the discount voucher code." });
  }

  // Spillage interactive choices if bot is asking about damage extent
  if ((textLower.includes("spill") || textLower.includes("leak") || textLower.includes("gravy")) && !chips.length) {
    chips.push({ label: "🍲 Entire Meal Damaged (100% Refund)", msg: "The gravy leaked completely and ruined the entire meal, making it inedible." });
    chips.push({ label: "🥣 Only Side Raita/Dip Leaked (Partial)", msg: "Only the side raita/dip leaked, the main dish is safe to eat." });
  }

  // Cold food / 25% courtesy refund options
  if ((textLower.includes("cold") || textLower.includes("lukewarm") || textLower.includes("25%")) && !chips.length) {
    chips.push({ label: "⚡ Accept 25% Wallet Credit", msg: "Yes, please credit the 25% courtesy refund to my wallet." });
    chips.push({ label: "🎟️ Claim Apology Voucher", msg: "I will take the apology voucher code for my next order." });
  }

  // Missing items
  if (textLower.includes("missing") && !chips.length) {
    chips.push({ label: "📦 Refund Missing Item Only", msg: "Please refund only the missing item value to my wallet." });
  }

  // Dynamically find any order IDs mentioned in response
  const ordMatches = textStr.match(/ORD-[A-Z0-9]+/g);
  if (ordMatches && ordMatches.length > 0) {
    const latestOrd = ordMatches[0];
    if (!textLower.includes("refund reference id") && !textLower.includes("refund method you chose") && !textLower.includes("cold")) {
      chips.push({ label: `🛵 Live Status of ${latestOrd}`, msg: `What is the live tracking status of order ${latestOrd}?` });
    }
  }

  if (meta.action === "clarify" || textLower.includes("which of these") || textLower.includes("what went wrong")) {
    chips.push({ label: "🍕 Food arrived cold", msg: "My order was delivered cold and late" });
    chips.push({ label: "📦 Items were missing", msg: "Several items were missing from my delivery" });
  }
  if (meta.action !== "escalate") {
    chips.push({ label: "🧑‍💼 Speak to Human Agent", msg: "I want to speak with a human agent immediately." });
  }

  let chipsHtml = "";
  if (chips.length > 0) {
    chipsHtml = `<div class="quick-action-chips">` + chips.map(c => 
      `<button class="chat-action-btn" onclick="window.sendQuickReply('${escHtml(c.msg)}')">${escHtml(c.label)}</button>`
    ).join("") + `</div>`;
  }

  row.innerHTML = `
    <div class="avatar bot-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
    </div>
    <div class="msg-content">
      <div class="bubble bot-bubble">
        ${resolutionCardHtml}
        ${voucherHtml}
        ${fmtMarkdown(textStr)}
      </div>
      ${chipsHtml}
      ${tagsHtml}
      ${escHtml_}
      <div class="msg-time">${now()}</div>
    </div>
  `;

  messages.appendChild(row);
  scrollDown();
}



window.sendQuickReply = function(msg) {
  if (IS_WAITING) return;
  userInput.value = msg;
  autoResize();
  chatForm.dispatchEvent(new Event("submit"));
};

function appendTyping() {
  const id = "typing-" + Date.now();
  const row = document.createElement("div");
  row.id = id;
  row.className = "msg-row bot typing";
  row.innerHTML = `
    <div class="avatar bot-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round">
        <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
      </svg>
    </div>
    <div class="msg-content">
      <div class="bubble bot-bubble">
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
      </div>
    </div>
  `;
  messages.appendChild(row);
  scrollDown();
  return id;
}

function removeTyping(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function scrollDown() {
  messages.scrollTo({ top: messages.scrollHeight, behavior: "smooth" });
}

function escHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function fmtMarkdown(text) {
  let html = escHtml(text);

  // Code blocks first
  html = html.replace(/```[\s\S]*?```/g, m => `<pre><code>${m.slice(3, -3)}</code></pre>`);

  // Horizontal rules
  html = html.replace(/^---$/gm, "<hr class='chat-divider'>");

  // Headings
  html = html.replace(/^### (.*$)/gm, "<h4 class='chat-h4'>$1</h4>");
  html = html.replace(/^## (.*$)/gm, "<h3 class='chat-h3'>$1</h3>");

  // Inline formatting
  html = html
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, "<code>$1</code>");

  // Tables
  html = html.replace(/((?:\|[^\n]+\|\r?\n)+)/g, (tableText) => {
    const lines = tableText.trim().split(/\r?\n/).filter(l => l.trim().startsWith("|"));
    if (lines.length < 2) return tableText;
    let tHtml = "<div class='table-responsive'><table class='chat-table'>";
    lines.forEach((line, idx) => {
      if (line.includes("---") || line.includes("&ndash;&ndash;")) return; // separator row
      const cells = line.split("|").slice(1, -1).map(c => c.trim());
      const tag = idx === 0 ? "th" : "td";
      tHtml += "<tr>" + cells.map(c => `<${tag}>${c}</${tag}>`).join("") + "</tr>";
    });
    tHtml += "</table></div>";
    return tHtml;
  });

  // Numbered lists
  html = html.replace(/((?:^\d+\.\s.+\n?)+)/gm, (block) => {
    const items = block.trim().split(/\n/).map(l => `<li>${l.replace(/^\d+\.\s/, "")}</li>`).join("");
    return `<ol>${items}</ol>`;
  });

  // Bullet lists
  html = html.replace(/((?:^[-•]\s.+\n?)+)/gm, (block) => {
    const items = block.trim().split(/\n/).map(l => `<li>${l.replace(/^[-•]\s/, "")}</li>`).join("");
    return `<ul>${items}</ul>`;
  });

  // Paragraphs
  html = html
    .replace(/\n\n+/g, "</p><p>")
    .replace(/\n/g, "<br>");

  return `<p>${html}</p>`;
}

// ═══════════════════════════════════════════════════
//   TAB SWITCHING & NAVIGATION
// ═══════════════════════════════════════════════════
function switchTab(tabName) {
  // Tabs
  document.querySelectorAll(".nav-tab").forEach(tab => tab.classList.remove("active"));
  const targetTab = document.getElementById(`tab-${tabName}`);
  if (targetTab) targetTab.classList.add("active");

  // Content
  document.querySelectorAll(".tab-content").forEach(content => content.classList.remove("active"));
  const targetView = document.getElementById(`view-${tabName}`);
  if (targetView) targetView.classList.add("active");

  if (tabName === "restaurants" && allRestaurants.length === 0) {
    loadRestaurants();
  } else if (tabName === "orders") {
    loadOrders();
  } else if (tabName === "chat") {
    scrollDown();
    setTimeout(() => {
      if (userInput) userInput.focus();
    }, 100);
  }
}

// ═══════════════════════════════════════════════════
//   RESTAURANT EXPLORER & 1-TAP QUICK ORDER
// ═══════════════════════════════════════════════════
let allRestaurants = [];
let currentCuisine = "All";
let currentSearch = "";
let searchDebounceTimer = null;
let lastPlacedOrder = null;

async function loadRestaurants(cuisine = currentCuisine, search = currentSearch) {
  const grid = document.getElementById("restaurants-grid");
  const countBadge = document.getElementById("rests-count-badge");
  const resultsMeta = document.getElementById("results-count");
  if (!grid) return;

  grid.innerHTML = '<div class="grid-loading">🍽️ Loading delicious restaurants & menus...</div>';

  try {
    let url = `/api/restaurants/?limit=100`;
    if (cuisine && cuisine !== "All") {
      url += `&cuisine=${encodeURIComponent(cuisine)}`;
    }
    if (search && search.trim()) {
      url += `&search=${encodeURIComponent(search.trim())}`;
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error("Failed to load restaurants");
    const data = await res.json();
    allRestaurants = data;

    if (countBadge) countBadge.textContent = `${data.length}+`;
    if (resultsMeta) resultsMeta.textContent = `Showing ${data.length} restaurant${data.length === 1 ? '' : 's'}`;

    if (data.length === 0) {
      grid.innerHTML = `
        <div class="grid-loading">
          <p style="font-size: 28px; margin-bottom: 8px;">🔍</p>
          <p>No restaurants found for "${escHtml(search || cuisine)}".</p>
          <button class="cat-chip" style="margin-top: 14px; display: inline-block;" onclick="filterCuisine('All')">Reset Filters</button>
        </div>
      `;
      return;
    }

    // Cuisine banner gradients / emojis
    const cuisineStyles = {
      "Biryani & Mughlai": { grad: "linear-gradient(135deg, #7c2d12, #451a03)", icon: "🍗" },
      "Pizza & Italian": { grad: "linear-gradient(135deg, #991b1b, #7f1d1d)", icon: "🍕" },
      "Burgers & American Fast Food": { grad: "linear-gradient(135deg, #b45309, #78350f)", icon: "🍔" },
      "North Indian & Mughlai": { grad: "linear-gradient(135deg, #854d0e, #713f12)", icon: "🍛" },
      "South Indian & Coastal": { grad: "linear-gradient(135deg, #166534, #14532d)", icon: "🥞" },
      "Chinese & Pan-Asian": { grad: "linear-gradient(135deg, #9f1239, #881337)", icon: "🥢" },
      "Healthy, Salads & Bowls": { grad: "linear-gradient(135deg, #065f46, #064e3b)", icon: "🥗" },
      "Desserts, Bakery & Cafes": { grad: "linear-gradient(135deg, #86198f, #701a75)", icon: "🍰" },
      "Street Food & Snacks": { grad: "linear-gradient(135deg, #c2410c, #9a3412)", icon: "🥟" }
    };

    grid.innerHTML = data.map(rest => {
      const cStyle = cuisineStyles[rest.cuisine_type] || { grad: "linear-gradient(135deg, #374151, #1f2937)", icon: "🍽️" };
      const rating = rest.rating ? Number(rest.rating).toFixed(1) : "4.5";
      const deliveryTime = rest.delivery_time_min ? `${rest.delivery_time_min} mins` : "25-35 mins";
      const priceForTwo = rest.min_order_amount ? `₹${Math.round(rest.min_order_amount * 2.5)} for two` : "₹350 for two";

      const menuHtml = (rest.menu_items || []).map(item => {
        const vegIcon = item.is_veg ? "🟢" : "🔴";
        const cleanName = escHtml(item.name).replace(/'/g, "\\'");
        return `
          <div class="dish-item">
            <div class="dish-info">
              <div class="dish-name-line">
                <span class="veg-icon" title="${item.is_veg ? 'Vegetarian' : 'Non-Vegetarian'}">${vegIcon}</span>
                <span>${escHtml(item.name)}</span>
              </div>
              <div class="dish-desc">${escHtml(item.description || item.category || '')}</div>
            </div>
            <button class="dish-order-btn" onclick="quickOrder('${rest.id}', '${cleanName}', ${item.price})">
              <span>Order</span> ₹${item.price}
            </button>
          </div>
        `;
      }).join("");

      return `
        <div class="restaurant-card" data-rest-id="${rest.id}">
          <div class="rest-card-banner" style="background: ${cStyle.grad};">
            <span class="rest-cuisine-badge">${cStyle.icon} ${escHtml(rest.cuisine_type || 'Multi-Cuisine')}</span>
            <span class="rest-rating-pill">⭐ ${rating}</span>
          </div>
          <div class="rest-card-body">
            <div class="rest-name-row">
              <h3 class="rest-name">${escHtml(rest.name)}</h3>
            </div>
            <div class="rest-meta-row">
              <span class="rest-meta-item">📍 ${escHtml(rest.address || 'Bengaluru')}</span>
              <span class="rest-meta-item">⏱️ ${deliveryTime}</span>
              <span class="rest-meta-item">💰 ${priceForTwo}</span>
            </div>
            <div class="menu-section-title">
              <span>Signature Dishes</span>
              <span>1-TAP QUICK ORDER</span>
            </div>
            <div class="dish-list">
              ${menuHtml || '<p style="color: var(--text-3); font-size: 12px;">Menu loading...</p>'}
            </div>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    grid.innerHTML = `
      <div class="grid-loading" style="color: #ef4444;">
        ⚠️ Failed to load restaurants: ${escHtml(err.message)}
        <br>
        <button class="cat-chip" style="margin-top: 14px;" onclick="loadRestaurants()">Retry</button>
      </div>
    `;
  }
}

function filterCuisine(cuisine) {
  currentCuisine = cuisine;
  document.querySelectorAll(".cat-chip").forEach(chip => {
    chip.classList.toggle("active", chip.textContent.includes(cuisine) || (cuisine === 'All' && chip.textContent.includes('All Places')));
  });
  loadRestaurants(currentCuisine, currentSearch);
}

function handleSearch(val) {
  clearTimeout(searchDebounceTimer);
  searchDebounceTimer = setTimeout(() => {
    currentSearch = val;
    loadRestaurants(currentCuisine, currentSearch);
  }, 250);
}

// ═══════════════════════════════════════════════════
//   1-TAP INSTANT QUICK ORDERING
// ═══════════════════════════════════════════════════
async function quickOrder(restaurantId, dishName, price) {
  try {
    const payload = {
      restaurant_id: restaurantId,
      dish_name: dishName,
      price: price,
      quantity: 1,
      delivery_address: "Flat 402, Green Glen Heights, Bellandur, Bengaluru",
      special_instructions: "Ring bell and leave at door",
      payment_method: "UPI"
    };

    const res = await fetch("/api/orders/quick-order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert("Order could not be placed: " + (err.detail || "Server error"));
      return;
    }

    const data = await res.json();
    const orderData = data.order || data;
    lastPlacedOrder = orderData;

    // Populate modal
    const modalDish = document.getElementById("modal-dish-name");
    const modalRest = document.getElementById("modal-rest-name");
    const modalId = document.getElementById("modal-order-id");
    const modalAmount = document.getElementById("modal-amount");
    const modalEta = document.getElementById("modal-eta");
    const modalDriver = document.getElementById("modal-driver");

    const amtStr = typeof orderData.total_amount === 'number' 
      ? `₹${orderData.total_amount.toFixed(2)}` 
      : (orderData.total_amount || '₹350.00');

    if (modalDish) modalDish.textContent = dishName;
    if (modalRest) modalRest.textContent = `from ${orderData.restaurant_name || 'Restaurant'}`;
    if (modalId) modalId.textContent = orderData.order_id;
    if (modalAmount) modalAmount.textContent = `${amtStr} (UPI Paid)`;
    if (modalEta) modalEta.textContent = `${orderData.eta_minutes || orderData.estimated_delivery || 30} mins`;
    if (modalDriver) modalDriver.textContent = `${orderData.driver_name || orderData.delivery_partner || 'Assigned Driver'} 🛵`;

    // Show modal
    const modal = document.getElementById("order-modal");
    if (modal) modal.style.display = "flex";

    // Update order count badge
    updateOrdersBadge();

  } catch (err) {
    alert("Error placing order: " + err.message);
  }
}

function closeOrderModal() {
  const modal = document.getElementById("order-modal");
  if (modal) modal.style.display = "none";
}

function goToTrackingFromModal() {
  closeOrderModal();
  switchTab("orders");
}

function askAiAboutOrderFromModal() {
  if (!lastPlacedOrder) return;
  const orderId = lastPlacedOrder.order_id;
  closeOrderModal();
  switchTab("chat");
  setTimeout(() => {
    submitChatQuery(`What is the live status and delivery partner details for my order ${orderId}?`);
  }, 200);
}

async function updateOrdersBadge() {
  try {
    const res = await fetch("/api/orders/list");
    if (res.ok) {
      const orders = await res.json();
      const badge = document.getElementById("orders-count-badge");
      if (badge) badge.textContent = orders.length;
    }
  } catch {}
}

// ═══════════════════════════════════════════════════
//   MY ORDERS & LIVE TRACKING VIEW
// ═══════════════════════════════════════════════════
async function loadOrders() {
  const container = document.getElementById("orders-list");
  if (!container) return;

  container.innerHTML = '<div class="grid-loading">🛵 Loading your orders and tracking status...</div>';

  try {
    const res = await fetch("/api/orders/list");
    if (!res.ok) throw new Error("Failed to load orders");
    const orders = await res.json();

    const badge = document.getElementById("orders-count-badge");
    if (badge) badge.textContent = orders.length;

    if (orders.length === 0) {
      container.innerHTML = `
        <div class="grid-loading">
          <p style="font-size: 32px; margin-bottom: 8px;">🍽️</p>
          <h3>No orders placed yet!</h3>
          <p style="color: var(--text-3); margin-top: 6px;">Browse 90+ restaurants and tap "Order" on any signature dish to see live tracking in action.</p>
          <button class="btn-primary" style="max-width: 220px; margin: 18px auto 0;" onclick="switchTab('restaurants')">
            Explore Restaurants
          </button>
        </div>
      `;
      return;
    }

    container.innerHTML = orders.map(order => {
      const status = order.status || "Placed";
      const statusKey = status.toLowerCase().replace(/\s+/g, "_");
      const orderDate = order.created_at || "Just now";

      // Stepper progress calculation
      const steps = ["Placed", "Confirmed", "Preparing", "Out for Delivery", "Delivered"];
      let stepIndex = steps.indexOf(status);
      if (stepIndex === -1 && (statusKey.includes("out") || statusKey.includes("delivery"))) stepIndex = 3;
      if (stepIndex === -1 && statusKey.includes("prep")) stepIndex = 2;
      if (stepIndex === -1) stepIndex = 2;

      const isDelivered = status === "Delivered" || statusKey === "delivered";
      const isCancelled = status === "Cancelled" || statusKey === "cancelled";

      let stepperHtml = "";
      if (!isCancelled) {
        stepperHtml = `
          <div class="order-stepper">
            <div class="stepper-line"></div>
            ${steps.map((st, idx) => {
              let cls = "";
              if (stepIndex > idx || isDelivered) cls = "completed";
              else if (stepIndex === idx) cls = "active";
              return `
                <div class="stepper-step ${cls}">
                  <div class="stepper-dot">${cls === "completed" ? "✓" : (idx + 1)}</div>
                  <div class="stepper-label">${st}</div>
                </div>
              `;
            }).join("")}
          </div>
        `;
      }

      // Items list
      const itemsList = (order.items || []).map(it => {
        const qty = it.qty || it.quantity || 1;
        const priceStr = typeof it.price === 'number' 
          ? `₹${(it.price * qty).toFixed(2)}` 
          : (it.price ? (it.price.toString().startsWith('₹') ? it.price : `₹${it.price}`) : '₹320.00');
        return `
          <div class="order-item-row">
            <span>${qty}x ${escHtml(it.name || it.item_name || 'Dish')}</span>
            <span>${priceStr}</span>
          </div>
        `;
      }).join("");

      const totalAmtStr = typeof order.total_amount === 'number' 
        ? `₹${order.total_amount.toFixed(2)}` 
        : (order.total_amount ? (order.total_amount.toString().startsWith('₹') ? order.total_amount : `₹${order.total_amount}`) : '₹350.00');

      const driverName = order.driver_name || order.delivery_partner || 'Assigning partner...';

      return `
        <div class="order-card" data-order-id="${order.order_id}">
          <div class="order-card-header">
            <div>
              <div class="order-id-badge">
                <span>📦 ${order.order_id}</span>
              </div>
              <div class="order-time-text">Placed on ${orderDate} · ${order.payment_method || 'UPI'}</div>
            </div>
            <span class="order-status-badge status-${statusKey}">${status}</span>
          </div>

          <div class="order-restaurant-info">
            <span style="font-size: 20px;">🍽️</span>
            <div>
              <div class="order-rest-name">${escHtml(order.restaurant_name || 'Restaurant')}</div>
              <div style="font-size: 12px; color: var(--text-3);">${escHtml(order.delivery_address || 'Bengaluru')}</div>
            </div>
          </div>

          ${stepperHtml}

          <div class="order-driver-box">
            <div class="driver-avatar">🛵</div>
            <div class="driver-info">
              <div class="driver-name">${escHtml(driverName)} (Delivery Partner)</div>
              <div class="driver-phone">📞 ${order.driver_phone || '+91 98112 34567'} · Live ETA: <strong>${order.estimated_delivery_at || order.estimated_delivery || '25 mins'}</strong></div>
            </div>
          </div>

          <div class="order-items-box">
            ${itemsList || `<div class="order-item-row"><span>1x ${escHtml(order.dish_name || 'Special Dish')}</span><span>${totalAmtStr}</span></div>`}
            <div class="order-total-row">
              <span>Total Paid</span>
              <span>${totalAmtStr}</span>
            </div>
          </div>

          ${!isDelivered && !isCancelled ? `
            <div class="simulate-deliver-bar">
              <button class="btn-simulate-deliver" onclick="simulateDelivery('${order.order_id}')">
                <span>🚀</span> Mark as Delivered (Simulate)
              </button>
            </div>
          ` : ''}

          ${isDelivered ? `
            <div class="delivered-notice-badge">
              <span>✅ Delivered Successfully</span>
              <span class="report-window-tag">⏳ 24h complaint window open</span>
            </div>
            <div class="delivered-complaint-box">
              <div class="complaint-box-header">
                <span>Any issues with your delivered food?</span>
                <button class="btn-complain-ai" onclick="complainAboutDeliveredOrder('${order.order_id}', '${escHtml((order.restaurant_name || '').replace(/'/g, "\\'"))}')">
                  💬 Complain to AI Agent
                </button>
              </div>
              <div class="complaint-quick-chips">
                <button class="comp-chip photo-chip" onclick="triggerDeliveredPhotoUpload('${order.order_id}', '${escHtml((order.restaurant_name || '').replace(/'/g, "\\'"))}')">📷 Upload Photo Proof (Refund)</button>
                <button class="comp-chip" onclick="complainWithReason('${order.order_id}', '${escHtml((order.restaurant_name || '').replace(/'/g, "\\'"))}', 'Food arrived cold & stale')">🍕 Cold Food</button>
                <button class="comp-chip" onclick="complainWithReason('${order.order_id}', '${escHtml((order.restaurant_name || '').replace(/'/g, "\\'"))}', 'Items are missing from my order')">📦 Missing Item</button>
                <button class="comp-chip" onclick="complainWithReason('${order.order_id}', '${escHtml((order.restaurant_name || '').replace(/'/g, "\\'"))}', 'Packaging was damaged and gravy spilled')">🥣 Spilled Gravy</button>
                <button class="comp-chip" onclick="complainWithReason('${order.order_id}', '${escHtml((order.restaurant_name || '').replace(/'/g, "\\'"))}', 'Poor food quality / spoiled food')">🤢 Bad Quality</button>
              </div>
            </div>
          ` : ''}

          <div class="order-actions-bar">
            <button class="btn-order-track" onclick="askAiAboutOrder('${order.order_id}', 'track')">
              <span>${isDelivered ? '📋' : '🛵'}</span> ${isDelivered ? 'Delivery Summary' : 'Track Status with AI'}
            </button>
            <button class="btn-order-refund" onclick="askAiAboutOrder('${order.order_id}', 'refund')">
              <span>💰</span> ${isDelivered ? 'Post-Delivery Refund' : 'Refund / Issue'}
            </button>
          </div>
        </div>
      `;
    }).join("");

  } catch (err) {
    container.innerHTML = `
      <div class="grid-loading" style="color: #ef4444;">
        ⚠️ Failed to load orders: ${escHtml(err.message)}
        <br>
        <button class="refresh-orders-btn" style="margin: 14px auto;" onclick="loadOrders()">Retry</button>
      </div>
    `;
  }
}

async function simulateDelivery(orderId) {
  try {
    const res = await fetch(`/api/orders/${orderId}/deliver`, { method: "POST" });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert("Failed to mark order as delivered: " + (err.detail || "Server error"));
      return;
    }
    // Refresh orders and show quick confirmation
    await loadOrders();
  } catch (err) {
    alert("Error simulating delivery: " + err.message);
  }
}

function complainAboutDeliveredOrder(orderId, restName) {
  switchTab("chat");
  setTimeout(() => {
    submitChatQuery(`My order ${orderId} from ${restName} was just delivered, but I have a complaint about the food quality and need a resolution.`);
  }, 200);
}

function triggerDeliveredPhotoUpload(orderId, restName) {
  switchTab("chat");
  setTimeout(() => {
    window.triggerPhotoDemo('spilled', orderId, restName);
  }, 200);
}

function complainWithReason(orderId, restName, reason) {
  switchTab("chat");
  setTimeout(() => {
    submitChatQuery(`My order ${orderId} from ${restName} was delivered, but ${reason}. Please process a refund or credit under the food quality policy.`);
  }, 200);
}

function askAiAboutOrder(orderId, actionType) {
  switchTab("chat");
  setTimeout(() => {
    let msg = "";
    if (actionType === "refund") {
      msg = `I want to request a refund for order ${orderId}. Can you check the policy and calculate my refund?`;
    } else {
      msg = `Where is my order ${orderId} right now? Can you give me the live tracking status and delivery partner details?`;
    }
    submitChatQuery(msg);
  }, 200);
}

function submitChatQuery(query) {
  userInput.value = query;
  autoResize();
  chatForm.dispatchEvent(new Event("submit"));
}

// ═══════════════════════════════════════════════════
//   SITUATION SCENARIO DEMO GENERATOR (Instant Testing)
// ═══════════════════════════════════════════════════
window.triggerPhotoDemo = window.triggerScenarioDemo = function(demoType, customOrderId = null, customRest = null) {
  switchTab("chat");

  const ordText = customOrderId ? `for my order ${customOrderId}${customRest ? ' from ' + customRest : ''}` : "for my delivered order";

  let promptText = "";
  if (demoType === "spilled") {
    promptText = `The curry packaging ${ordText} leaked all over the bag and ruined the meal. Can I get a full refund?`;
  } else if (demoType === "burnt") {
    promptText = `My food ${ordText} arrived severely burnt, charred and inedible. Please process a refund.`;
  } else if (demoType === "cold") {
    promptText = `My delivered food ${ordText} arrived completely cold and late. Can I get courtesy wallet credit?`;
  } else if (demoType === "melted") {
    promptText = `My ice cream dessert ${ordText} arrived completely melted and warm! What is your zero-melt policy?`;
  } else if (demoType === "dietary") {
    promptText = `I strictly ordered pure veg, but received a non-veg chicken dish ${ordText}! Please help immediately!`;
  } else {
    promptText = `I have an issue ${ordText} and would like to request assistance with a refund.`;
  }

  submitChatQuery(promptText);
};

// ═══════════════════════════════════════════════════
//   INITIALIZATION ON PAGE LOAD
// ═══════════════════════════════════════════════════
window.addEventListener("DOMContentLoaded", () => {
  loadRestaurants();
  updateOrdersBadge();
});


