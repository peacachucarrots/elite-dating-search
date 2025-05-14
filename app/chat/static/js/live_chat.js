//  static/js/_live_chat.js
(() => {
  /* ---------- DOM hooks ---------- */
  const chatBox  = document.getElementById("chatbox");
  if (!chatBox) return;

  const messages = chatBox.querySelector("#messages");
  const form     = chatBox.querySelector("#chatForm");
  const input    = chatBox.querySelector("#msgInput");
  const toggle   = chatBox.querySelector(".toggle");

  /* ---------- constants ---------- */
  const OPEN_KEY    = "chatboxOpen";          // 'true' | 'false'
  const LOG_KEY     = "chatboxLog";           // JSON array of {who,text}
  const MAX_STORED  = 200;                    // rotate oldest beyond this

  /* ---------- restore message log ---------- */
  const saved = JSON.parse(localStorage.getItem(LOG_KEY) || "[]");
  saved.forEach(({ who, text }) => append(who, text, false));   // false=no save

  /* ---------- Socket.IO ---------- */
  const socket = io({ transports: ["websocket", "polling"] });

  socket.on("rep_msg", (m) => append("rep", m));
  socket.on("system",  (m) => append("sys", m));
  socket.on("disconnect", () => append("sys", "Chat Disconnected…"));

  /* ---------- send flow ---------- */
  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const text = input.value.trim();
    if (!text) return;
    socket.emit("visitor_msg", text);
    append("me", text);
    input.value = "";
  });

  /* ---------- append helper (and persist) ---------- */
  function append(who, text, persist = true) {
    const div = document.createElement("div");
    div.className = `msg ${who}`;
    div.textContent = text;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;

    if (persist) {
      saved.push({ who, text });
      if (saved.length > MAX_STORED) saved.shift();             // trim
      localStorage.setItem(LOG_KEY, JSON.stringify(saved));
    }
  }

  /* ---------- open/close persister ---------- */
  let isOpen = localStorage.getItem(OPEN_KEY) === "true";
  if (isOpen) chatBox.classList.remove("collapsed");
  toggle.textContent = isOpen ? "▼" : "▲";

  toggle.addEventListener("click", () => {
    isOpen = !chatBox.classList.toggle("collapsed");
    toggle.textContent = isOpen ? "▼" : "▲";
    localStorage.setItem(OPEN_KEY, isOpen);
  });
})();