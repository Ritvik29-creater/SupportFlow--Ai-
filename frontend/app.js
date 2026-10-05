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
  confidence: document.getElementById("node-confidence"),
};
const descs = {
  guard:      document.getElementById("desc-guard"),
  sentiment:  document.getElementById("desc-sentiment"),
  intent:     document.getElementById("desc-intent"),
  rag:        document.getElementById("desc-rag"),
  specialist: document.getElementById("desc-specialist"),
  confidence: document.getElementById("desc-confidence"),
};

// Side panel refs
const confCard      = document.getElementById("conf-card");
const confFill      = document.getElementById("conf-fill");
const confPct       = document.getElementById("conf-pct");
const intentCard    = document.getElementById("intent-card");
const intentBadge   = document.getElementById("intent-badge");
const sentimentCard = document.getElementById("sentiment-card");
const sentimentBadge= document.getElementById("sentiment-badge");
const statusInd     = document.getElementById("status-indicator");
const statusLabel   = document.getElementById("status-label");

// ── Intent metadata ───────────────────────────────────────────────────────────
const INTENT_META = {
  order_tracking:   { icon: "🛵", label: "Order Tracking",   agent: "Order Agent",    color: "#f59e0b" },
  payment:          { icon: "💳", label: "Payment Issue",    agent: "Payment Agent",  color: "#3b82f6" },
  refund:           { icon: "💰", label: "Refund Request",   agent: "Refund Agent",   color: "#22c55e" },
  restaurant:       { icon: "🍽️", label: "Restaurant Issue", agent: "Restaurant Agent", color: "#f97316" },
  delivery_partner: { icon: "🚴", label: "Delivery Partner", agent: "Partner Agent",  color: "#ef4444" },
  account_app:      { icon: "📱", label: "Account & App",    agent: "App Agent",      color: "#8b5cf6" },
  coupon_offer:     { icon: "🎟️", label: "Coupon & Offers",  agent: "Offers Agent",   color: "#ec4899" },
  general_support:  { icon: "📚", label: "General Support",  agent: "RAG Agent",      color: "#94a3b8" },
  unknown:          { icon: "❓", label: "Analyzing...",      agent: "RAG Agent",      color: "#94a3b8" },
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
sidebarToggle.addEventListener("click", () => {
  sidebar.classList.toggle("open");
});

document.addEventListener("click", (e) => {
  if (sidebar.classList.contains("open") &&
      !sidebar.contains(e.target) && e.target !== sidebarToggle) {
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
      body: JSON.stringify({ content: query, session_id: SESSION_ID }),
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
  }

  IS_WAITING = false;
  sendBtn.disabled = false;
  userInput.focus();
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

function animatePipeline() {
  resetPipeline();

  const schedule = (fn, delay) => {
    const t = setTimeout(fn, delay);
    _pipelineTimers.push(t);
  };

  // Guard → immediate
  setNodeState("guard", "running", "Scanning input...");
  schedule(() => {
    setNodeState("guard", "done", "Input safe");
    setNodeState("sentiment", "running", "Analyzing emotion...");
  }, 300);
  schedule(() => {
    setNodeState("sentiment", "done", "Emotion detected");
    setNodeState("intent", "running", "Classifying intent...");
  }, 700);
  schedule(() => {
    setNodeState("intent", "done", "Intent classified");
    setNodeState("rag", "running", "Searching policies...");
  }, 1200);
  schedule(() => {
    setNodeState("rag", "done", "Docs retrieved");
    setNodeState("specialist", "running", "Generating answer...");
  }, 1800);
  // specialist and confidence complete when response arrives
}

function finishPipeline(data) {
  _pipelineTimers.forEach(clearTimeout);
  _pipelineTimers = [];

  const intent = data.intent || "general_support";
  const meta = INTENT_META[intent] || INTENT_META.general_support;

  setNodeState("specialist", "done", "Answer generated");
  setNodeState("confidence", "running", "Scoring quality...");

  const isEscalate = data.action === "escalate";

  setTimeout(() => {
    setNodeState("confidence", isEscalate ? "error" : "done",
      isEscalate ? "Escalating to human" : "High quality answer");

    // Update specialist node info
    const specIcon = document.getElementById("specialist-icon");
    const specName = document.getElementById("specialist-name");
    if (specIcon) specIcon.textContent = meta.icon;
    if (specName) specName.textContent = meta.agent;

    // Confidence meter
    if (data.confidence !== null && data.confidence !== undefined) {
      const pct = Math.round(data.confidence * 100);
      confCard.style.display = "block";
      confPct.textContent = pct + "%";
      setTimeout(() => { confFill.style.width = pct + "%"; }, 50);
    }

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
      <div class="bubble user-bubble">${escHtml(text)}</div>
      <div class="msg-time">${now()}</div>
    </div>
  `;
  messages.appendChild(row);
  scrollDown();
}

function appendBotMsg(text, meta = {}) {
  const row = document.createElement("div");
  row.className = "msg-row bot";

  const intent = meta.intent || "general_support";
  const intMeta = INTENT_META[intent] || INTENT_META.general_support;

  // Tags
  const tags = [];
  if (meta.intent && meta.intent !== "unknown") {
    tags.push(`<span class="tag tag-intent">${intMeta.icon} ${intMeta.label}</span>`);
  }
  if (meta.confidence !== null && meta.confidence !== undefined) {
    const pct = Math.round(meta.confidence * 100);
    const cls = pct >= 70 ? "" : pct >= 45 ? " mid" : " low";
    tags.push(`<span class="tag tag-confidence${cls}">🎯 ${pct}%</span>`);
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
        <div class="esc-info">Ticket ${meta.ticket_id} · Human will respond within 2–4 hrs</div>
      </div>`;
  }

  // Contextual quick action buttons
  const chips = [];
  const textLower = text.toLowerCase();
  if (text.includes("ORD-84512") && !textLower.includes("refund reference id") && !textLower.includes("refund method you chose")) {
    chips.push({ label: "⚡ Refund ORD-84512 to Wallet", msg: "Yes, please refund ORD-84512 to my wallet" });
    chips.push({ label: "💳 Refund to Original Payment", msg: "Please refund ORD-84512 to my original card" });
  }
  if (text.includes("ORD-90210")) {
    chips.push({ label: "🛵 Live Status of ORD-90210", msg: "What is the status of my order ORD-90210?" });
    chips.push({ label: "📞 Contact Delivery Partner", msg: "What is the driver contact for ORD-90210?" });
  }
  if (meta.action === "clarify" || textLower.includes("which of these") || textLower.includes("what went wrong")) {
    chips.push({ label: "🍕 Food arrived cold", msg: "My order was ORD-84512 and it was delivered cold" });
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
      <div class="bubble bot-bubble">${fmtMarkdown(text)}</div>
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
