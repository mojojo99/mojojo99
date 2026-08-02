/**
 * Embeddable sales chat widget.
 *
 * Add to any page of your website:
 *   <script src="https://YOUR-BOT-SERVER/widget/chat.js" defer></script>
 *
 * Optional attributes:
 *   <script src=".../chat.js" defer
 *           data-title="Chat with us"
 *           data-color="#1a3c6e"></script>
 */
(function () {
  "use strict";

  var script = document.currentScript;
  var BASE = script ? new URL(script.src).origin : "";
  var TITLE = (script && script.dataset.title) || "Chat with us 👋";
  var COLOR = (script && script.dataset.color) || "#1a3c6e";
  var GREETING =
    (script && script.dataset.greeting) ||
    "Hi! Ask me anything about our Leadership Training and Teambuilding programmes.";

  var sessionId = null;
  try {
    sessionId = localStorage.getItem("salesbot_session");
  } catch (e) {}

  // ── Styles ────────────────────────────────────────────────────────────────
  var css =
    "#sb-bubble{position:fixed;bottom:24px;right:24px;width:60px;height:60px;border-radius:50%;background:" + COLOR + ";color:#fff;border:none;cursor:pointer;box-shadow:0 4px 16px rgba(0,0,0,.25);font-size:26px;z-index:99998;display:flex;align-items:center;justify-content:center}" +
    "#sb-panel{position:fixed;bottom:96px;right:24px;width:360px;max-width:calc(100vw - 32px);height:520px;max-height:calc(100vh - 120px);background:#fff;border-radius:14px;box-shadow:0 8px 32px rgba(0,0,0,.3);display:none;flex-direction:column;overflow:hidden;z-index:99999;font-family:system-ui,-apple-system,Segoe UI,sans-serif}" +
    "#sb-panel.open{display:flex}" +
    "#sb-head{background:" + COLOR + ";color:#fff;padding:14px 16px;font-weight:600;font-size:15px}" +
    "#sb-msgs{flex:1;overflow-y:auto;padding:14px;background:#f5f7fa;display:flex;flex-direction:column;gap:8px}" +
    ".sb-msg{max-width:85%;padding:9px 12px;border-radius:12px;font-size:14px;line-height:1.45;white-space:pre-wrap;word-wrap:break-word}" +
    ".sb-bot{background:#fff;border:1px solid #e2e8f0;align-self:flex-start;border-bottom-left-radius:4px}" +
    ".sb-user{background:" + COLOR + ";color:#fff;align-self:flex-end;border-bottom-right-radius:4px}" +
    ".sb-msg a{color:" + COLOR + "}.sb-user a{color:#fff}" +
    "#sb-form{display:flex;border-top:1px solid #e2e8f0;background:#fff}" +
    "#sb-input{flex:1;border:none;padding:13px 14px;font-size:14px;outline:none;font-family:inherit}" +
    "#sb-send{border:none;background:none;color:" + COLOR + ";font-weight:700;padding:0 16px;cursor:pointer;font-size:14px}" +
    ".sb-typing{opacity:.6;font-style:italic}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  // ── DOM ───────────────────────────────────────────────────────────────────
  var bubble = document.createElement("button");
  bubble.id = "sb-bubble";
  bubble.setAttribute("aria-label", "Open chat");
  bubble.textContent = "💬";

  var panel = document.createElement("div");
  panel.id = "sb-panel";
  panel.innerHTML =
    '<div id="sb-head"></div>' +
    '<div id="sb-msgs"></div>' +
    '<form id="sb-form"><input id="sb-input" placeholder="Type your message…" autocomplete="off"><button id="sb-send" type="submit">Send</button></form>';

  document.body.appendChild(bubble);
  document.body.appendChild(panel);
  panel.querySelector("#sb-head").textContent = TITLE;

  var msgs = panel.querySelector("#sb-msgs");
  var form = panel.querySelector("#sb-form");
  var input = panel.querySelector("#sb-input");

  function linkify(text) {
    var div = document.createElement("div");
    div.textContent = text; // escape HTML first
    return div.innerHTML.replace(
      /(https?:\/\/[^\s<]+)/g,
      '<a href="$1" target="_blank" rel="noopener">$1</a>'
    );
  }

  function add(role, text) {
    var el = document.createElement("div");
    el.className = "sb-msg sb-" + role;
    el.innerHTML = linkify(text);
    msgs.appendChild(el);
    msgs.scrollTop = msgs.scrollHeight;
    return el;
  }

  bubble.addEventListener("click", function () {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) {
      if (!msgs.children.length) add("bot", GREETING);
      input.focus();
    }
  });

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    add("user", text);
    var typing = add("bot", "…");
    typing.classList.add("sb-typing");

    fetch(BASE + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_id: sessionId }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        sessionId = data.session_id;
        try { localStorage.setItem("salesbot_session", sessionId); } catch (e) {}
        typing.classList.remove("sb-typing");
        typing.innerHTML = linkify(data.reply);
        msgs.scrollTop = msgs.scrollHeight;
      })
      .catch(function () {
        typing.classList.remove("sb-typing");
        typing.textContent = "Sorry, I couldn't connect. Please try again.";
      });
  });
})();
